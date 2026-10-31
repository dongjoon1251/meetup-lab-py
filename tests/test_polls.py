import pytest
from helpers import VOTE_CLOSES_AT, at

from meetup_lab.polls import service
from meetup_lab.store import store


def votes_by_name(event_id="EVT-01"):
    return {r.name: r.votes for r in service.results(event_id).results}


def test_cast_vote_records_vote_with_server_time():
    vote = service.cast_vote("EVT-01", "M-01", "MENU-1", now=at(minutes=1))
    assert vote.voted_at == at(minutes=1)
    assert store.get_vote("EVT-01", "M-01") == vote


def test_results_count_votes_per_menu_including_zero():
    service.cast_vote("EVT-01", "M-01", "MENU-1", now=at(minutes=1))
    service.cast_vote("EVT-01", "M-02", "MENU-2", now=at(minutes=2))
    service.cast_vote("EVT-01", "M-03", "MENU-1", now=at(minutes=3))
    assert votes_by_name() == {"피자": 2, "김밥": 1, "샌드위치": 0}


def test_revote_overwrites_previous_vote():
    service.cast_vote("EVT-01", "M-01", "MENU-1", now=at(minutes=1))
    service.cast_vote("EVT-01", "M-01", "MENU-3", now=at(minutes=2))
    assert votes_by_name() == {"피자": 0, "김밥": 0, "샌드위치": 1}


def test_vote_one_second_before_close_is_accepted():
    service.cast_vote("EVT-01", "M-01", "MENU-1", now=at(hours=24, seconds=-1))
    assert votes_by_name()["피자"] == 1


def test_vote_at_close_is_rejected():
    with pytest.raises(service.VotingClosed):
        service.cast_vote("EVT-01", "M-01", "MENU-1", now=VOTE_CLOSES_AT)


def test_vote_one_second_after_close_is_rejected():
    with pytest.raises(service.VotingClosed):
        service.cast_vote("EVT-01", "M-01", "MENU-1", now=at(hours=24, seconds=1))


def test_vote_for_unknown_option_is_rejected():
    with pytest.raises(service.OptionNotFound):
        service.cast_vote("EVT-01", "M-01", "MENU-9", now=at(minutes=1))


def test_results_for_unknown_event_is_rejected():
    with pytest.raises(service.EventNotFound):
        service.results("EVT-99")
