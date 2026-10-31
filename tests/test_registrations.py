"""과제 ① 인수조건: 현재 상태는 저장소에서 다시 읽는다(모델은 복사 저장)."""
import pytest
from helpers import at

from meetup_lab.models import RegistrationEventType as Kind, RegistrationStatus as Status
from meetup_lab.registrations.service import (
    DuplicateRegistration, EventNotFound, RegistrationNotFound, service,
)
from meetup_lab.store import store


def register_members(*members, event_id="EVT-01"):
    return [service.register(event_id, m, now=at(minutes=i)) for i, m in enumerate(members)]


def test_capacity_boundary_and_server_sequence():
    regs = register_members("M-01", "M-02", "M-03", "M-04", "M-05")
    assert [r.seq for r in regs] == [1, 2, 3, 4, 5]
    assert [r.status for r in regs] == [Status.CONFIRMED] * 3 + [Status.WAITLISTED] * 2


@pytest.mark.parametrize("member", ["M-01", "M-04"])
def test_active_duplicate_is_409_without_extra_history(member):
    register_members("M-01", "M-02", "M-03", "M-04")
    before = len(store.list_history("EVT-01"))
    with pytest.raises(DuplicateRegistration) as exc:
        service.register("EVT-01", member, now=at(hours=1))
    assert exc.value.status_code == 409
    assert len(store.list_history("EVT-01")) == before
    assert len(store.list_registrations("EVT-01")) == 4


def test_cancel_twice_promotes_only_one():
    regs = register_members("M-01", "M-02", "M-03", "M-04", "M-05")
    service.cancel(regs[2].id, now=at(hours=1))
    service.cancel(regs[2].id, now=at(hours=1, seconds=1))
    assert store.get_registration(regs[3].id).status == Status.CONFIRMED
    assert store.get_registration(regs[4].id).status == Status.WAITLISTED
    history = store.list_history("EVT-01")
    assert sum(h.type == Kind.CANCELLED for h in history) == 1
    assert sum(h.type == Kind.PROMOTED for h in history) == 1
    assert next(h.at for h in history if h.type == Kind.PROMOTED) == at(hours=1)


def test_cancel_waitlisted_does_not_promote():
    regs = register_members("M-01", "M-02", "M-03", "M-04", "M-05")
    service.cancel(regs[3].id, now=at(hours=1))
    assert store.get_registration(regs[4].id).status == Status.WAITLISTED
    assert not any(h.type == Kind.PROMOTED for h in store.list_history("EVT-01"))


def test_wait_order_uses_seq_even_with_same_timestamp():
    regs = [service.register("EVT-01", f"M-{i:02}", now=at()) for i in range(1, 6)]
    service.cancel(regs[0].id, now=at(hours=1))
    assert store.get_registration(regs[3].id).status == Status.CONFIRMED
    assert store.get_registration(regs[4].id).status == Status.WAITLISTED


def test_other_event_is_isolated():
    event = store.get_event("EVT-01").model_copy(update={"id": "EVT-02", "capacity": 1})
    store.add_event(event, [])
    other = register_members("M-01", "M-02", event_id="EVT-02")
    regs = register_members("M-01", "M-02", "M-03", "M-04")
    service.cancel(regs[0].id, now=at(hours=1))
    assert [r.status for r in store.list_registrations("EVT-02")] == [Status.CONFIRMED, Status.WAITLISTED]
    assert store.get_registration(other[1].id).status == Status.WAITLISTED


def test_cancelled_member_can_register_again_with_new_seq():
    (old,) = register_members("M-01")
    service.cancel(old.id, now=at(hours=1))
    new = service.register("EVT-01", "M-01", now=at(hours=2))
    assert new.id != old.id
    assert new.seq > old.seq
    assert new.status == Status.CONFIRMED


def test_every_registration_has_one_registered_event_including_waitlist():
    register_members("M-01", "M-02", "M-03", "M-04")
    history = store.list_history("EVT-01")
    assert sum(h.type == Kind.REGISTERED for h in history) == 4
    assert sum(h.type == Kind.WAITLISTED for h in history) == 1


def test_unknown_event_and_registration_are_404():
    with pytest.raises(EventNotFound):
        service.register("EVT-99", "M-01", now=at())
    with pytest.raises(RegistrationNotFound):
        service.cancel("REG-99", now=at())
