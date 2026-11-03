import os
import subprocess
import sys
from pathlib import Path

import pytest

from meetup_lab.replay_log import parse_line, read_log

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"


def test_parse_line_reads_time_action_event_member():
    line = parse_line("2026-10-26T09:00:01+09:00 cancel   EVT-01 M-03   # 같은 취소 재요청")
    assert (line.at.isoformat(), line.action, line.event_id, line.member_id, line.note) == (
        "2026-10-26T09:00:01+09:00", "cancel", "EVT-01", "M-03", "같은 취소 재요청",
    )


def test_parse_line_skips_comment_and_blank():
    assert parse_line("# 시각(KST) 동작 행사 회원") is None
    assert parse_line("   ") is None


def test_parse_line_rejects_unknown_action():
    with pytest.raises(ValueError):
        parse_line("2026-10-26T09:00:00+09:00 promote EVT-01 M-03")


def test_sample_logs_parse():
    assert len(read_log(SAMPLES / "basic.log")) == 4
    assert len(read_log(SAMPLES / "waitlist.log")) == 8


def test_check_registration_basic_log_has_no_waitlist_or_promotion():
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_registration.py"), str(SAMPLES / "basic.log")],
        capture_output=True, text=True, encoding="utf-8", check=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},  # 한글 Windows(cp949)에서도 UTF-8 로 받기
    ).stdout
    assert "참가 2명 · 대기 0명 · 취소 1명 · 승격 0건" in out
