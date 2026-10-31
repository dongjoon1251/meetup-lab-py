import pytest
from helpers import at

from meetup_lab.models import RegistrationEventType, RegistrationStatus
from meetup_lab.registrations.service import (
    CapacityExceeded,
    EventNotFound,
    RegistrationNotFound,
    service,
)
from meetup_lab.store import store


def register_members(*members, event_id="EVT-01"):
    return [service.register(event_id, m, now=at(minutes=i)) for i, m in enumerate(members)]


def history_types(event_id="EVT-01"):
    return [h.type for h in store.list_history(event_id)]


def test_register_under_capacity_is_confirmed_with_seq():
    regs = register_members("M-01", "M-02", "M-03")
    assert [(r.id, r.seq, r.status) for r in regs] == [
        ("REG-1", 1, RegistrationStatus.CONFIRMED),
        ("REG-2", 2, RegistrationStatus.CONFIRMED),
        ("REG-3", 3, RegistrationStatus.CONFIRMED),
    ]
    assert regs[0].created_at == at(minutes=0)


def test_register_over_capacity_is_rejected():
    # 이슈 #1 구현 전 동작 — 정원(3)이 차면 409 정원 초과
    register_members("M-01", "M-02", "M-03")
    with pytest.raises(CapacityExceeded):
        service.register("EVT-01", "M-04", now=at(minutes=10))
    assert len(store.list_registrations("EVT-01")) == 3


def test_register_unknown_event_is_rejected():
    with pytest.raises(EventNotFound):
        service.register("EVT-99", "M-01", now=at(minutes=1))


def test_cancel_marks_cancelled_and_records_history():
    (reg,) = register_members("M-01")
    cancelled = service.cancel(reg.id, now=at(hours=1))
    assert cancelled.status == RegistrationStatus.CANCELLED
    assert store.get_registration(reg.id).status == RegistrationStatus.CANCELLED
    assert history_types() == [RegistrationEventType.REGISTERED, RegistrationEventType.CANCELLED]
    assert store.list_history("EVT-01")[-1].at == at(hours=1)


def test_cancel_twice_keeps_single_cancel_history():
    (reg,) = register_members("M-01")
    service.cancel(reg.id, now=at(hours=1))
    again = service.cancel(reg.id, now=at(hours=1, seconds=1))
    assert again.status == RegistrationStatus.CANCELLED
    assert history_types().count(RegistrationEventType.CANCELLED) == 1


def test_cancel_frees_a_seat():
    regs = register_members("M-01", "M-02", "M-03")
    service.cancel(regs[1].id, now=at(hours=1))
    reg = service.register("EVT-01", "M-04", now=at(hours=2))
    assert (reg.seq, reg.status) == (4, RegistrationStatus.CONFIRMED)


def test_cancel_unknown_registration_is_rejected():
    with pytest.raises(RegistrationNotFound):
        service.cancel("REG-99", now=at(minutes=1))
