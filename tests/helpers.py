"""테스트용 고정 시각. 테스트는 datetime.now() 대신 T0 / at() 만 쓴다."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

# conftest 가 이 시각으로 seed 를 적재한다 → EVT-01 투표 마감 = T0 + 24시간
T0 = datetime(2026, 10, 25, 1, 0, tzinfo=timezone.utc)  # 2026-10-25 10:00 KST


def at(**delta: float) -> datetime:
    """T0 기준 상대 시각. 예: at(minutes=5), at(hours=24, seconds=-1)"""
    return T0 + timedelta(**delta)


VOTE_CLOSES_AT = at(hours=24)
