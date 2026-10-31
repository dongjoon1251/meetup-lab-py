from helpers import at


def post_vote(client, voter_id, option_id, event_id="EVT-01"):
    return client.post(f"/events/{event_id}/votes", json={"voter_id": voter_id, "option_id": option_id})


def register(client, member_id, event_id="EVT-01", **headers):
    return client.post(f"/events/{event_id}/registrations", json={"member_id": member_id}, headers=headers)


def test_status_page_is_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "meetup-lab" in r.text


def test_registrations_have_fields_used_by_status_page(client):
    register(client, "M-01")
    (row,) = client.get("/events/EVT-01/registrations").json()
    assert {"seq", "member_id", "status"} <= row.keys()


# --- health · events ----------------------------------------------------------


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_list_events(client):
    events = client.get("/events").json()
    assert [(e["id"], e["title"], e["capacity"]) for e in events] == [("EVT-01", "10월 스터디 정기 모임", 3)]


def test_get_event(client):
    assert client.get("/events/EVT-01").json()["vote_closes_at"] == "2026-10-26T01:00:00Z"


def test_get_unknown_event_is_404(client):
    assert client.get("/events/EVT-99").status_code == 404


# --- polls --------------------------------------------------------------------


def test_get_menu(client):
    menu = client.get("/events/EVT-01/menu").json()
    assert [(m["id"], m["name"]) for m in menu] == [("MENU-1", "피자"), ("MENU-2", "김밥"), ("MENU-3", "샌드위치")]


def test_demo_votes_give_pizza_2_kimbap_1_sandwich_0(client):
    for voter_id, option_id in [("M-01", "MENU-1"), ("M-02", "MENU-2"), ("M-03", "MENU-1")]:
        assert post_vote(client, voter_id, option_id).status_code == 201
    assert client.get("/events/EVT-01/votes/results").json() == {
        "event_id": "EVT-01",
        "results": [
            {"option_id": "MENU-1", "name": "피자", "votes": 2},
            {"option_id": "MENU-2", "name": "김밥", "votes": 1},
            {"option_id": "MENU-3", "name": "샌드위치", "votes": 0},
        ],
    }


def test_vote_uses_server_time(client, set_now):
    set_now(at(minutes=30))
    assert post_vote(client, "M-01", "MENU-1").json()["voted_at"] == "2026-10-25T01:30:00Z"


def test_vote_after_close_is_409(client, set_now):
    set_now(at(hours=24))
    assert post_vote(client, "M-01", "MENU-1").status_code == 409


def test_vote_unknown_option_is_404(client):
    assert post_vote(client, "M-01", "MENU-9").status_code == 404


def test_vote_missing_field_is_422(client):
    assert client.post("/events/EVT-01/votes", json={"voter_id": "M-01"}).status_code == 422


def test_results_unknown_event_is_404(client):
    assert client.get("/events/EVT-99/votes/results").status_code == 404


# --- registrations -------------------------------------------------------------


def test_register_returns_201_confirmed(client):
    body = register(client, "M-01").json()
    assert (body["id"], body["seq"], body["status"], body["created_at"]) == ("REG-1", 1, "CONFIRMED", "2026-10-25T01:00:00Z")


def test_register_over_capacity_is_409(client):
    # 이슈 #1 구현 전 동작 — 정원(3)이 차면 409 정원 초과
    for member_id in ("M-01", "M-02", "M-03"):
        register(client, member_id)
    r = register(client, "M-04")
    assert (r.status_code, r.json()["detail"]) == (409, "정원 초과")


def test_register_unknown_event_is_404(client):
    assert register(client, "M-01", event_id="EVT-99").status_code == 404


def test_register_missing_member_is_422(client):
    assert client.post("/events/EVT-01/registrations", json={}).status_code == 422


def test_replay_header_sets_record_time(client):
    body = register(client, "M-01", **{"X-Replay-At": "2026-10-26T00:50:00+09:00"}).json()
    assert body["created_at"] == "2026-10-25T15:50:00Z"


def test_cancel_registration(client):
    reg_id = register(client, "M-01").json()["id"]
    r = client.delete(f"/registrations/{reg_id}")
    assert (r.status_code, r.json()["status"]) == (200, "CANCELLED")


def test_cancel_unknown_registration_is_404(client):
    assert client.delete("/registrations/REG-99").status_code == 404


def test_list_registrations_in_seq_order(client):
    for member_id in ("M-02", "M-01"):
        register(client, member_id)
    regs = client.get("/events/EVT-01/registrations").json()
    assert [(r["member_id"], r["seq"]) for r in regs] == [("M-02", 1), ("M-01", 2)]


def test_list_registrations_unknown_event_is_404(client):
    assert client.get("/events/EVT-99/registrations").status_code == 404
