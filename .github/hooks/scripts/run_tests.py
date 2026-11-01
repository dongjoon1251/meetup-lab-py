"""Return UTC pytest evidence to the model after file edits."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
# VS Code starts hooks with the system Python, which has no pytest; prefer the lab venv.
PYTHON = next((str(p) for p in (ROOT / '.venv/Scripts/python.exe', ROOT / '.venv/bin/python')
               if p.exists()), sys.executable)


def main() -> None:
    # Consume the event; never treat tool output as a command to run.
    try:
        json.load(sys.stdin)
    except (ValueError, TypeError):
        pass
    env = os.environ.copy()
    env.update(TZ='UTC', PYTHONPATH=str(ROOT / 'src'), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
               PYTHONDONTWRITEBYTECODE='1')
    try:
        result = subprocess.run([PYTHON, '-m', 'pytest', '-q'], cwd=ROOT,
                                env=env, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=150)
        summary = f'exit={result.returncode}\n{result.stdout[-16000:]}'
    except (OSError, subprocess.TimeoutExpired) as exc:
        summary = f'테스트 실행 실패: {exc}'
    context = ('[Harness] UTC 시간대 pytest\n' + summary +
               '\n관계없는 실패면 고치지 말고 보고만 하세요. M6 전 day_range 알려진 실패 한 건은 유지합니다.')
    with (ROOT / '.github/hooks/hook.log').open('a', encoding='utf-8') as stream:
        stream.write('postToolUse pytest(UTC): ' + summary.replace('\n', ' ')[-2000:] + '\n')
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'postToolUse',
                                            'additionalContext': context}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
