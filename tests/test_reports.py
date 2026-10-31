from datetime import date, datetime, timedelta

from helpers import KST

from meetup_lab.reports.registrations import day_range


def test_day_range_is_one_day_long():
    start, end = day_range(date(2026, 10, 26))
    assert end - start == timedelta(days=1)


def test_day_range_includes_early_morning_kst():
    # 10월 26일 오전 1시 KST 신청은 10월 26일(KST 하루) 집계에 들어가야 한다
    start, end = day_range(date(2026, 10, 26))
    signed_up = datetime(2026, 10, 26, 1, 0, tzinfo=KST)
    assert start <= signed_up
    assert signed_up < end
