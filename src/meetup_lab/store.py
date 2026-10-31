"""메모리 저장소 — 행사·메뉴·투표·신청·상태 변경 이력을 들고 있다 (DB 없음).

다른 모듈은 저장 구조(dict)를 직접 만지지 말고 이 모듈의 메서드로만 읽고 쓴다.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from meetup_lab.models import (
    Event,
    MenuOption,
    Registration,
    RegistrationEvent,
    Vote,
    utcnow,
)

SEED_PATH = Path(os.environ.get("MEETUP_SEED", Path(__file__).resolve().parents[2] / "data" / "seed.json"))


class Store:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """모든 데이터를 비운다. 테스트는 conftest 가 매번 호출한다."""
        self._events: dict[str, Event] = {}
        self._menus: dict[str, list[MenuOption]] = {}
        self._votes: dict[tuple[str, str], Vote] = {}
        self._registrations: dict[str, Registration] = {}
        self._history: list[RegistrationEvent] = []
        self._last_seq = 0

    def load_seed(self, path: Path = SEED_PATH, now: datetime | None = None) -> None:
        """seed.json 을 적재한다. 투표 마감·행사 시작은 `now`(기본: 지금) 기준 상대 시간이다."""
        now = now or utcnow()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for e in data["events"]:
            self.add_event(
                Event(
                    id=e["id"],
                    title=e["title"],
                    capacity=e["capacity"],
                    starts_at=now + timedelta(hours=e["starts_in_hours"]),
                    vote_closes_at=now + timedelta(hours=e["vote_closes_in_hours"]),
                ),
                [MenuOption(id=m["id"], event_id=e["id"], name=m["name"]) for m in e["menu"]],
            )

    # --- 행사 · 메뉴 ---------------------------------------------------------

    def add_event(self, event: Event, menu: list[MenuOption]) -> None:
        self._events[event.id] = event
        self._menus[event.id] = list(menu)

    def get_event(self, event_id: str) -> Event | None:
        return self._events.get(event_id)

    def list_events(self) -> list[Event]:
        return list(self._events.values())

    def list_menu(self, event_id: str) -> list[MenuOption]:
        return list(self._menus.get(event_id, []))

    def get_option(self, event_id: str, option_id: str) -> MenuOption | None:
        return next((m for m in self._menus.get(event_id, []) if m.id == option_id), None)

    # --- 투표 ---------------------------------------------------------------

    def save_vote(self, vote: Vote) -> None:
        """(event_id, voter_id) 당 한 표만 둔다 — 다시 저장하면 이전 표를 덮어쓴다."""
        self._votes[(vote.event_id, vote.voter_id)] = vote

    def get_vote(self, event_id: str, voter_id: str) -> Vote | None:
        return self._votes.get((event_id, voter_id))

    def list_votes(self, event_id: str) -> list[Vote]:
        return [v for (eid, _), v in self._votes.items() if eid == event_id]

    # --- 신청 · 이력 -----------------------------------------------------------

    def next_seq(self) -> int:
        """신청 순번을 하나 발급한다. 대기 순서는 이 값으로 정한다."""
        self._last_seq += 1
        return self._last_seq

    def save_registration(self, registration: Registration) -> None:
        self._registrations[registration.id] = registration

    def get_registration(self, registration_id: str) -> Registration | None:
        return self._registrations.get(registration_id)

    def list_registrations(self, event_id: str) -> list[Registration]:
        regs = [r for r in self._registrations.values() if r.event_id == event_id]
        return sorted(regs, key=lambda r: r.seq)

    def add_history(self, event: RegistrationEvent) -> None:
        self._history.append(event)

    def list_history(self, event_id: str) -> list[RegistrationEvent]:
        return [h for h in self._history if h.event_id == event_id]


store = Store()
