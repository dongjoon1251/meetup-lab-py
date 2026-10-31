"""신청 현황 리포트. 행사별 일일 집계 API 는 이슈 #2(`docs/issues/02-registration-report.md`)에서 만든다."""

from datetime import date, datetime, timedelta


def day_range(day: date) -> tuple[datetime, datetime]:
    """`day` 하루의 [시작, 끝) 시각을 돌려준다."""
    start = datetime(day.year, day.month, day.day).astimezone()
    return start, start + timedelta(days=1)


def registration_report(event_id: str, from_date: date, to_date: date) -> dict:
    """Count REGISTERED once per new registration, including waitlisted ones.

    WAITLISTED is supplementary status history and is not another signup.

    day_range deliberately retains the local-timezone bug for the M6 CI lab.
    The range is inclusive; days without history are returned with zero counts.
    """
    from meetup_lab.store import store

    if store.get_event(event_id) is None:
        raise LookupError(f"행사 없음: {event_id}")
    if from_date > to_date:
        raise ValueError("from must be on or before to")
    history = store.list_history(event_id)
    fields = {"REGISTERED": "registered",
              "CANCELLED": "cancelled", "PROMOTED": "promoted"}
    days = []
    day = from_date
    while day <= to_date:
        start, end = day_range(day)
        counts = dict(date=day.isoformat(), registered=0, cancelled=0, promoted=0)
        for entry in history:
            if start <= entry.at < end and entry.type in fields:
                counts[fields[entry.type]] += 1
        days.append(counts)
        if day == to_date:
            break
        day += timedelta(days=1)
    return {"event_id": event_id, "days": days}
