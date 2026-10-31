---
applyTo: "tests/**/*.py"
---
- `tests/helpers.py`의 T0·at()로 시각을 주입하고 conftest의 store reset을 사용한다.
- 정원 경계·중복 신청 409·seq 순서·취소 재요청·행사 격리를 검증한다.
- 새 기능의 실패 테스트를 먼저 작성하고 기존 테스트의 기대값을 낮추지 않는다.
- 외부 HTTP는 모의한다. 실제 웹훅을 호출하지 않는다.
- Asia/Seoul 및 UTC에서 전체 pytest를 실행한다. M6 전에는 알려진 day_range 실패 한 건만 허용한다.
