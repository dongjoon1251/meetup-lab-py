---
name: debug-failure
description: 실패한 테스트·에러 로그의 원인을 좁히고 최소 수정안을 제시한다. "/debug-failure" 뒤에 실패 출력을 붙여 직접 실행한다.
disable-model-invocation: true
---
# 실패 원인 찾기

1. 붙여 넣은 출력에서 **첫 번째** 실패의 테스트 이름·파일·줄을 찾는다.
2. 그 테스트와 테스트가 호출하는 함수만 읽는다(전체 검색 금지).
3. 원인을 한 문장으로 쓴다: "기대값 X, 실제값 Y, 이유 Z".
4. 최소 수정안을 diff 로 제시하고, 같은 원인으로 깨질 다른 테스트가 있는지 1줄로 적는다.

## 규칙
- 테스트를 지우거나 기대값을 바꿔 통과시키지 않는다(명시적 요청이 있을 때만).
- 시간 관련 실패는 `$env:TZ="UTC0"; python -m pytest -q; Remove-Item Env:TZ` (mac/Linux `TZ=UTC python -m pytest -q`) 로 재현 가능한지 먼저 확인한다.
- 수정은 사람이 승인한 뒤에만 파일에 반영한다.
