"""과제 ① 정답: 신청 순번 기반 대기 등록·자동 승격. 동시성 보강은 M6 리뷰."""

import logging
from datetime import datetime, timezone

from meetup_lab.models import (
    Registration,
    RegistrationEvent,
    RegistrationEventType,
    RegistrationStatus,
    utcnow,
)
from meetup_lab.store import Store, store

logger = logging.getLogger(__name__)


class RegistrationError(Exception):
    status_code = 400


class EventNotFound(RegistrationError):
    status_code = 404


class RegistrationNotFound(RegistrationError):
    status_code = 404


class DuplicateRegistration(RegistrationError):
    status_code = 409


class RegistrationService:
    def __init__(self, store: Store = store) -> None:
        self.store = store

    def register(self, event_id: str, member_id: str, now: datetime | None = None) -> Registration:
        """참가 신청. 활성 중복은 409, 정원이 차면 WAITLISTED."""
        event = self.store.get_event(event_id)
        if event is None:
            raise EventNotFound(f"행사 없음: {event_id}")

        now = (now or utcnow()).astimezone(timezone.utc)  # UTC 로 저장
        registrations = self.store.list_registrations(event_id)
        if any(r.member_id == member_id and r.status != RegistrationStatus.CANCELLED for r in registrations):
            raise DuplicateRegistration("중복 신청")
        confirmed = [r for r in self.store.list_registrations(event_id) if r.status == RegistrationStatus.CONFIRMED]
        status = RegistrationStatus.CONFIRMED if len(confirmed) < event.capacity else RegistrationStatus.WAITLISTED

        seq = self.store.next_seq()
        registration = Registration(
            id=f"REG-{seq}",
            seq=seq,
            event_id=event_id,
            member_id=member_id,
            status=status,
            created_at=now,
        )
        self.store.save_registration(registration)
        self._record(registration, RegistrationEventType.REGISTERED, now)
        if status == RegistrationStatus.WAITLISTED:
            self._record(registration, RegistrationEventType.WAITLISTED, now)
        logger.info("registered %s %s %s (seq %d)", registration.id, event_id, member_id, seq)
        return registration

    def cancel(self, registration_id: str, now: datetime | None = None) -> Registration:
        """신청 취소. 이미 취소한 신청은 그대로 돌려준다(이력 추가 없음)."""
        registration = self.store.get_registration(registration_id)
        if registration is None:
            raise RegistrationNotFound(f"신청 없음: {registration_id}")
        if registration.status == RegistrationStatus.CANCELLED:
            return registration

        now = (now or utcnow()).astimezone(timezone.utc)  # UTC 로 저장
        cancelled = registration.model_copy(update={"status": RegistrationStatus.CANCELLED})
        self.store.save_registration(cancelled)
        self._record(cancelled, RegistrationEventType.CANCELLED, now)
        logger.info("cancelled %s %s %s", cancelled.id, cancelled.event_id, cancelled.member_id)
        if registration.status == RegistrationStatus.CONFIRMED:
            waiting = [r for r in self.store.list_registrations(registration.event_id)
                       if r.status == RegistrationStatus.WAITLISTED]
            if waiting:
                first = min(waiting, key=lambda r: r.seq)
                promoted = first.model_copy(update={"status": RegistrationStatus.CONFIRMED})
                self.store.save_registration(promoted)
                self._record(promoted, RegistrationEventType.PROMOTED, now)
        return cancelled

    def list(self, event_id: str) -> list[Registration]:
        if self.store.get_event(event_id) is None:
            raise EventNotFound(f"행사 없음: {event_id}")
        return self.store.list_registrations(event_id)

    def _record(self, registration: Registration, type_: RegistrationEventType, at: datetime) -> None:
        self.store.add_history(
            RegistrationEvent(registration_id=registration.id, event_id=registration.event_id, type=type_, at=at)
        )


service = RegistrationService()
