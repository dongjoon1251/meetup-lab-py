"""신청 기록 파일(`data/samples/*.log`) 읽기 — 한 줄 = 요청 1건, `#` 뒤는 설명.

    2026-10-26T00:50:00+09:00 register EVT-01 M-01
    2026-10-26T09:00:00+09:00 cancel   EVT-01 M-03   # 같은 취소 재요청
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ACTIONS = ("register", "cancel")


@dataclass(frozen=True)
class LogLine:
    at: datetime  # 기록 파일의 시각 (timezone 포함)
    action: str  # register | cancel
    event_id: str
    member_id: str
    note: str = ""


def parse_line(text: str) -> LogLine | None:
    """한 줄을 읽는다. 빈 줄·설명 줄은 None."""
    body, _, note = text.partition("#")
    parts = body.split()
    if not parts:
        return None
    if len(parts) != 4 or parts[1] not in ACTIONS:
        raise ValueError(f"기록 형식 오류: {text.strip()!r}")
    at = datetime.fromisoformat(parts[0])
    if at.tzinfo is None:
        raise ValueError(f"시각에 시간대가 없음: {parts[0]}")
    return LogLine(at=at, action=parts[1], event_id=parts[2], member_id=parts[3], note=note.strip())


def read_log(path: str | Path) -> list[LogLine]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [line for line in map(parse_line, lines) if line is not None]
