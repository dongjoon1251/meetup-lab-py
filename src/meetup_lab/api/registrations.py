from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException

from meetup_lab.models import Registration, RegistrationRequest, utcnow
from meetup_lab.registrations.service import RegistrationError, service

router = APIRouter(tags=["registrations"])


def request_time(
    x_replay_at: datetime | None = Header(default=None, include_in_schema=False),
    now: datetime = Depends(utcnow),
) -> datetime:
    """서버 기록 시각. `scripts/seed_demo.py --replay` 만 기록 파일의 시각을 X-Replay-At 헤더로 넘긴다."""
    return x_replay_at or now


@router.post("/events/{event_id}/registrations", response_model=Registration, status_code=201)
def post_registration(
    event_id: str, body: RegistrationRequest, now: datetime = Depends(request_time)
) -> Registration:
    try:
        return service.register(event_id, body.member_id, now=now)
    except RegistrationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.delete("/registrations/{registration_id}", response_model=Registration)
def delete_registration(registration_id: str, now: datetime = Depends(request_time)) -> Registration:
    try:
        return service.cancel(registration_id, now=now)
    except RegistrationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/events/{event_id}/registrations", response_model=list[Registration])
def list_registrations(event_id: str) -> list[Registration]:
    try:
        return service.list(event_id)
    except RegistrationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
