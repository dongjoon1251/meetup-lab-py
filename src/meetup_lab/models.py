"""도메인 모델과 API 요청·응답 모델.

시각은 모두 timezone 이 붙은 UTC 로 저장한다. 날짜 단위 집계만 KST(Asia/Seoul) 하루 기준이다.
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    """서버가 기록하는 현재 시각(UTC). 테스트는 이 함수를 의존성 override 로 바꾼다."""
    return datetime.now(timezone.utc)


class RegistrationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    WAITLISTED = "WAITLISTED"
    CANCELLED = "CANCELLED"


class RegistrationEventType(str, Enum):
    REGISTERED = "REGISTERED"
    WAITLISTED = "WAITLISTED"
    CANCELLED = "CANCELLED"
    PROMOTED = "PROMOTED"


class Event(BaseModel):
    id: str
    title: str
    capacity: int
    starts_at: datetime
    vote_closes_at: datetime


class MenuOption(BaseModel):
    id: str
    event_id: str
    name: str


class Vote(BaseModel):
    """1인 1표 — 같은 (event_id, voter_id) 로 다시 투표하면 덮어쓴다."""

    event_id: str
    voter_id: str
    option_id: str
    voted_at: datetime


class Registration(BaseModel):
    id: str
    seq: int  # 서버가 발급한 신청 순번 — 대기 순서의 기준
    event_id: str
    member_id: str
    status: RegistrationStatus
    created_at: datetime


class RegistrationEvent(BaseModel):
    """신청 상태 변경 이력 한 건. 일별 집계(이슈 #2)는 현재 상태가 아니라 이 이력으로 센다."""

    registration_id: str
    event_id: str
    type: RegistrationEventType
    at: datetime


# --- API 요청·응답 ---------------------------------------------------------


class VoteRequest(BaseModel):
    voter_id: str = Field(min_length=1)
    option_id: str = Field(min_length=1)


class OptionResult(BaseModel):
    option_id: str
    name: str
    votes: int


class PollResults(BaseModel):
    event_id: str
    results: list[OptionResult]


class RegistrationRequest(BaseModel):
    member_id: str = Field(min_length=1)
