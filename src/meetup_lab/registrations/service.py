"""행사 신청·취소 규칙.

지금은 정원이 차면 신청을 거절(409)한다. 대기 등록과 자동 승격은 이슈 #1
(`docs/issues/01-waitlist-promotion.md`) 에서 구현한다.
"""

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


class CapacityExceeded(RegistrationError):
    status_code = 409


class RegistrationService:
    def __init__(self, store: Store = store) -> None:
        self.store = store

    def register(self, event_id: str, member_id: str, now: datetime | None = None) -> Registration:
        """참가 신청. 정원 미만이면 CONFIRMED, 정원이 찼으면 CapacityExceeded."""
        event = self.store.get_event(event_id)
        if event is None:
            raise EventNotFound(f"행사 없음: {event_id}")

        now = (now or utcnow()).astimezone(timezone.utc)  # UTC 로 저장
        confirmed = [r for r in self.store.list_registrations(event_id) if r.status == RegistrationStatus.CONFIRMED]
        if len(confirmed) >= event.capacity:
            raise CapacityExceeded("정원 초과")

        seq = self.store.next_seq()
        registration = Registration(
            id=f"REG-{seq}",
            seq=seq,
            event_id=event_id,
            member_id=member_id,
            status=RegistrationStatus.CONFIRMED,
            created_at=now,
        )
        self.store.save_registration(registration)
        self._record(registration, RegistrationEventType.REGISTERED, now)
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
