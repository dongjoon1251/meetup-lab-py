"""Keep merging in the human approval step of the M6 lab."""
import json
import re
import sys

from block_dangerous import ROOT, TERMINAL, commands


def main() -> None:
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError('hook input must be an object')
        name = str(event.get('toolName', event.get('tool_name', '')))
        deny = bool(re.search(r'merge_pull_request|mergePullRequest', name, re.I) or
                    (TERMINAL.search(name) and any(
                        re.search(r'\b(?:gh\b[^\n;&|]*\bpr\s+merge|git\b[^\n;&|]*\bmerge)\b',
                                  command, re.I) for command in commands(event))))
    except (ValueError, TypeError):
        deny = True
    output = {'hookSpecificOutput': {'hookEventName': 'preToolUse'}}
    if deny:
        output['hookSpecificOutput'].update(
            permissionDecision='deny',
            permissionDecisionReason='Harness: merge는 사람이 PR·CI·리뷰를 확인하고 명시적으로 승인하여 GitHub에서 직접 수행하세요.')
    with (ROOT / '.github/hooks/hook.log').open('a', encoding='utf-8') as stream:
        stream.write(f'preToolUse merge-guard deny={deny}\n')
    print(json.dumps(output))  # ASCII JSON: 한글 Windows 에서도 안 깨짐


if __name__ == '__main__':
    main()
