"""Educational guardrail for direct dangerous terminal commands, not a shell sandbox."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
TERMINAL = re.compile(r'terminal|bash|powershell|shell|exec_command|execute|run_command', re.I)
DANGEROUS = (
    r'\bgit\b[^\n;&|]*\bpush\b[^\n;&|]*(?:--force(?:-with-lease|-if-includes)?\b|-[a-zA-Z]*f[a-zA-Z]*\b|(?:^|\s)\+\S+)',
    r'\bgit\b[^\n;&|]*\breset\b[^\n;&|]*--hard\b',
    r'\bgit\b[^\n;&|]*\bclean\b[^\n;&|]*(?:-[a-zA-Z]*f[a-zA-Z]*|--force)\b',
    r'\brm\b[^\n;&|]*(?:\s-[a-zA-Z]*[rR][a-zA-Z]*|\s--recursive)\b',
    r'\b(?:Remove-Item|ri|del|erase)\b[^\n;&|]*\s-(?:Recurse|r)\b',
)


def commands(value: object) -> list[str]:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (ValueError, TypeError):
            return [value]
        return commands(decoded) if not isinstance(decoded, str) else [decoded]
    if isinstance(value, dict):
        result = []
        for key in ('command', 'cmd', 'script', 'input', 'tool_input', 'toolInput', 'toolArgs', 'arguments'):
            if key in value:
                result.extend(commands(value[key]))
        return result
    if isinstance(value, list):
        return [part for item in value for part in commands(item)]
    return []


def main() -> None:
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError('hook input must be an object')
        name = str(event.get('toolName', event.get('tool_name', '')))
        deny = bool(TERMINAL.search(name) and any(
            re.search(pattern, command, re.I)
            for command in commands(event) for pattern in DANGEROUS))
        reason = 'Harness: 강제 push·hard reset·강제 clean·재귀 삭제는 실행하지 않습니다.'
    except (ValueError, TypeError):
        name, deny, reason = 'invalid-input', True, 'Harness: hook JSON 입력을 해석할 수 없습니다.'
    log = ROOT / '.github/hooks/hook.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('a', encoding='utf-8') as stream:
        stream.write(f'preToolUse {name} deny={deny}\n')
    output = {'hookSpecificOutput': {'hookEventName': 'preToolUse'}}
    if deny:
        output['hookSpecificOutput'].update(permissionDecision='deny', permissionDecisionReason=reason)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == '__main__':
    main()
