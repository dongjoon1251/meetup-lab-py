"""신청 기록 파일을 서비스에 직접 흘려 각 줄의 결과·상태·대기 순서를 표로 출력한다 (서버 불필요).

    python scripts/check_registration.py data/samples/waitlist.log

각 줄의 시각을 서비스에 주입(now=)하고, 줄마다 다른 신청의 상태가 바뀌었으면(승격 등) 함께 보여 준다.
"""

import argparse
import sys
import unicodedata
from zoneinfo import ZoneInfo

from meetup_lab.models import Registration, RegistrationEventType, RegistrationStatus
from meetup_lab.registrations.service import RegistrationError, service
from meetup_lab.replay_log import LogLine, read_log
from meetup_lab.store import store

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

KST = ZoneInfo("Asia/Seoul")
WIDTHS = (19, 8, 5, 15, 10, 3)


def row(*cells: str) -> str:
    """한글 폭(2칸)을 고려해 열을 맞춘다. 마지막 칸은 맞추지 않는다."""
    out = []
    for cell, width in zip(cells, WIDTHS):
        shown = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in cell)
        out.append(cell + " " * max(width - shown, 0))
    return "  ".join(out + list(cells[len(WIDTHS):]))


def find_registration(line: LogLine) -> Registration | None:
    """취소 대상: 그 회원의 가장 최근 신청."""
    mine = [r for r in store.list_registrations(line.event_id) if r.member_id == line.member_id]
    return mine[-1] if mine else None


def snapshot(event_id: str) -> dict[str, Registration]:
    return {r.id: r for r in store.list_registrations(event_id)}


def apply(line: LogLine) -> tuple[str, Registration | None]:
    try:
        if line.action == "register":
            return "201", service.register(line.event_id, line.member_id, now=line.at)
        target = find_registration(line)
        if target is None:
            return "404 신청 없음", None
        return "200", service.cancel(target.id, now=line.at)
    except RegistrationError as e:
        return f"{e.status_code} {e}", None


def changes(before: dict[str, Registration], after: dict[str, Registration], target: Registration | None) -> str:
    """대상 신청을 뺀 나머지 중 상태가 바뀐 신청 (예: 승격)."""
    moved = [
        f"{r.member_id} {before[r.id].status.value}→{r.status.value}"
        for r in after.values()
        if r.id in before and before[r.id].status != r.status and (target is None or r.id != target.id)
    ]
    return ", ".join(moved) if moved else "-"


def main() -> int:
    parser = argparse.ArgumentParser(description="신청 기록 재생 → 상태·대기 순서 표")
    parser.add_argument("log", help="기록 파일 (예: data/samples/waitlist.log)")
    args = parser.parse_args()

    lines = read_log(args.log)
    store.reset()
    store.load_seed(now=lines[0].at if lines else None)

    print(row("시각(KST)", "동작", "회원", "결과", "상태", "seq", "다른 신청 변화(승격 등)"))
    for line in lines:
        before = snapshot(line.event_id)
        result, registration = apply(line)
        status = registration.status.value if registration else "-"
        seq = str(registration.seq) if registration else "-"
        moved = changes(before, snapshot(line.event_id), registration)
        when = line.at.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")
        note = f"  # {line.note}" if line.note else ""
        print(row(when, line.action, line.member_id, result, status, seq, moved) + note)

    for event_id in sorted({line.event_id for line in lines}):
        regs = store.list_registrations(event_id)
        count = {s: sum(r.status == s for r in regs) for s in RegistrationStatus}
        promoted = sum(h.type == RegistrationEventType.PROMOTED for h in store.list_history(event_id))
        print(f"\n최종 상태 — {event_id}")
        for r in regs:
            print(f"  {r.member_id}  {r.status.value:<11} seq {r.seq}")
        print(
            f"참가 {count[RegistrationStatus.CONFIRMED]}명 · 대기 {count[RegistrationStatus.WAITLISTED]}명 · "
            f"취소 {count[RegistrationStatus.CANCELLED]}명 · 승격 {promoted}건"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
