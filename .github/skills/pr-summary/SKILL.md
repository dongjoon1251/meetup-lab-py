---
name: pr-summary
description: 현재 브랜치의 변경을 PR 템플릿 형식으로 요약한다. "/pr-summary" 로 직접 실행한다.
disable-model-invocation: true
---
# PR 설명 초안 만들기

1. `git diff main...HEAD --stat` 과 `git log main..HEAD --oneline` 으로 변경 범위를 확인한다.
2. `.github/pull_request_template.md` 의 항목(이슈 · 변경 요약 · 테스트 방법)을 그대로 채운다.
3. 변경 요약은 "무엇을 · 왜" 3줄 이내, 파일 나열 금지.
4. 테스트 방법에는 실제로 실행한 명령과 결과(예: `pytest -q` → `N passed`, `check_registration.py` 의 최종 상태 줄)만 쓴다. 실행하지 않은 것은 "미실행"으로 적는다.

## 규칙
- 코드는 수정하지 않는다. 결과는 채팅에 Markdown 으로만 출력한다.
- 커밋 메시지·diff 에 없는 내용(성능 향상, 리팩터링 등)을 지어내지 않는다.
