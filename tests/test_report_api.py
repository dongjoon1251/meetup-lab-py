from datetime import datetime, timedelta, timezone

import pytest

from meetup_lab.models import RegistrationEvent
from meetup_lab.store import store
from meetup_lab.registrations.service import RegistrationService


def test_report_counts_history_and_zero_days(client):
    # Noon KST: WAITLISTED is auxiliary history, not a second registration.
    for kind, day, event in [("REGISTERED", 25, "EVT-01"), ("WAITLISTED", 25, "EVT-01"),
                             ("CANCELLED", 26, "EVT-01"), ("PROMOTED", 26, "EVT-01"),
                             ("REGISTERED", 25, "OTHER"), ("REGISTERED", 24, "EVT-01")]:
        store.add_history(RegistrationEvent(registration_id="REG-history", event_id=event,
                          type=kind, at=datetime(2026, 10, day, 3, tzinfo=timezone.utc)))
    response = client.get('/reports/registrations', params={
        'event_id': 'EVT-01', 'from': '2026-10-25', 'to': '2026-10-27'})
    assert response.status_code == 200
    assert response.json() == {'event_id': 'EVT-01', 'days': [
        {'date': '2026-10-25', 'registered': 1, 'cancelled': 0, 'promoted': 0},
        {'date': '2026-10-26', 'registered': 0, 'cancelled': 1, 'promoted': 1},
        {'date': '2026-10-27', 'registered': 0, 'cancelled': 0, 'promoted': 0}]}


@pytest.mark.parametrize('params,code', [
    ({'event_id': 'missing', 'from': '2026-10-25', 'to': '2026-10-26'}, 404),
    ({'event_id': 'EVT-01', 'from': '2026-10-27', 'to': '2026-10-25'}, 422),
    ({'event_id': 'EVT-01', 'from': 'bad', 'to': '2026-10-25'}, 422),
    ({'event_id': 'EVT-01'}, 422),
])
def test_report_invalid_requests(client, params, code):
    assert client.get('/reports/registrations', params=params).status_code == code


def test_report_with_real_waitlist_promotion_and_repeated_cancel(client):
    service = RegistrationService(store)
    noon = datetime(2026, 10, 26, 3, tzinfo=timezone.utc)  # 12:00 KST, same UTC date
    registrations = [service.register("EVT-01", f"M-{i}", now=noon + timedelta(minutes=i))
                     for i in range(1, 6)]
    assert [r.status for r in registrations] == ["CONFIRMED"] * 3 + ["WAITLISTED"] * 2
    assert sum(h.type == "WAITLISTED" for h in store.list_history("EVT-01")) == 2
    service.cancel(registrations[2].id, now=noon + timedelta(hours=1))
    assert store.get_registration(registrations[3].id).status == "CONFIRMED"
    before_retry = store.list_history("EVT-01")
    service.cancel(registrations[2].id, now=noon + timedelta(hours=1, seconds=1))
    assert store.list_history("EVT-01") == before_retry
    assert store.get_registration(registrations[4].id).status == "WAITLISTED"
    service.cancel(registrations[4].id, now=noon + timedelta(hours=2))
    response = client.get("/reports/registrations", params={
        "event_id": "EVT-01", "from": "2026-10-26", "to": "2026-10-26"})
    assert response.status_code == 200
    assert response.json() == {"event_id": "EVT-01", "days": [
        {"date": "2026-10-26", "registered": 5, "cancelled": 2, "promoted": 1}]}
