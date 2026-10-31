"""신청 현황 리포트. 행사별 일일 집계 API 는 이슈 #2(`docs/issues/02-registration-report.md`)에서 만든다."""

from datetime import date, datetime, timedelta


def day_range(day: date) -> tuple[datetime, datetime]:
    """`day` 하루의 [시작, 끝) 시각을 돌려준다."""
    start = datetime(day.year, day.month, day.day).astimezone()
    return start, start + timedelta(days=1)
