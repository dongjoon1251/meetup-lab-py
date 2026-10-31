"""메뉴 투표 규칙 — 1인 1표(다시 투표하면 덮어쓰기), 마감 시각 정각부터 거절."""

from datetime import datetime, timezone

from meetup_lab.models import OptionResult, PollResults, Vote, utcnow
from meetup_lab.store import store


class PollError(Exception):
    status_code = 400


class EventNotFound(PollError):
    status_code = 404


class OptionNotFound(PollError):
    status_code = 404


class VotingClosed(PollError):
    status_code = 409


def cast_vote(event_id: str, voter_id: str, option_id: str, now: datetime | None = None) -> Vote:
    """투표를 기록한다. `now` 는 서버 기록 시각(기본: 지금)."""
    event = store.get_event(event_id)
    if event is None:
        raise EventNotFound(f"행사 없음: {event_id}")
    if store.get_option(event_id, option_id) is None:
        raise OptionNotFound(f"메뉴 없음: {option_id}")

    now = (now or utcnow()).astimezone(timezone.utc)  # UTC 로 저장
    if now >= event.vote_closes_at:  # 마감 정각도 거절
        raise VotingClosed("투표 마감")

    vote = Vote(event_id=event_id, voter_id=voter_id, option_id=option_id, voted_at=now)
    store.save_vote(vote)  # 같은 투표자의 이전 표는 덮어쓴다
    return vote


def results(event_id: str) -> PollResults:
    """메뉴별 득표 수. 메뉴 순서대로, 표가 없는 메뉴도 0 으로 포함한다."""
    if store.get_event(event_id) is None:
        raise EventNotFound(f"행사 없음: {event_id}")

    counts: dict[str, int] = {}
    for vote in store.list_votes(event_id):
        counts[vote.option_id] = counts.get(vote.option_id, 0) + 1

    return PollResults(
        event_id=event_id,
        results=[
            OptionResult(option_id=m.id, name=m.name, votes=counts.get(m.id, 0))
            for m in store.list_menu(event_id)
        ],
    )
