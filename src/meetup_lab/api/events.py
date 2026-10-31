from fastapi import APIRouter, HTTPException

from meetup_lab.models import Event
from meetup_lab.store import store

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[Event])
def list_events() -> list[Event]:
    return store.list_events()


@router.get("/{event_id}", response_model=Event)
def get_event(event_id: str) -> Event:
    event = store.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"행사 없음: {event_id}")
    return event
