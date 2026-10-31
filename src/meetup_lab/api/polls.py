from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from meetup_lab.models import MenuOption, PollResults, Vote, VoteRequest, utcnow
from meetup_lab.polls import service
from meetup_lab.store import store

router = APIRouter(prefix="/events/{event_id}", tags=["polls"])


@router.get("/menu", response_model=list[MenuOption])
def get_menu(event_id: str) -> list[MenuOption]:
    if store.get_event(event_id) is None:
        raise HTTPException(status_code=404, detail=f"행사 없음: {event_id}")
    return store.list_menu(event_id)


@router.post("/votes", response_model=Vote, status_code=201)
def post_vote(event_id: str, body: VoteRequest, now: datetime = Depends(utcnow)) -> Vote:
    """투표. 시각은 요청 값이 아니라 서버 기록 시각(UTC)을 쓴다."""
    try:
        return service.cast_vote(event_id, body.voter_id, body.option_id, now=now)
    except service.PollError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/votes/results", response_model=PollResults)
def get_results(event_id: str) -> PollResults:
    try:
        return service.results(event_id)
    except service.PollError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
