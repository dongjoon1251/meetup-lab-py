---
name: pr-create
description: 실제 변경과 테스트 근거로 PR 초안을 만들고 승인 후 push와 PR 생성을 수행한다.
disable-model-invocation: true
---
1. git diff·브랜치 이력·실제 관련 이슈를 확인한다. base는 main이다.
2. .github/pull_request_template.md의 칸을 그대로 채운다. 제목은 Conventional Commits 한 줄이다.
3. 구현된 이슈만 Closes #<번호>로 각각 연결한다. 기본 과정 예는 #1·#2·#4지만 실제 번호를 확인한다.
4. 테스트 방법에 python -m pytest -q와 python scripts/check_registration.py data/samples/waitlist.log를 넣는다.
5. 미실행 테스트·미확인 CI를 통과했다고 쓰지 않는다. 초안을 사람에게 보여 승인받는다.
6. push와 GitHub MCP PR 생성은 각각 승인된 후에만 실행한다. 실제 PR URL과 CI 상태를 보고한다.
승인 없이 merge하지 않는다. 이미지 게시를 배포라고 부르지 않는다. Jira 작업을 만들어 냈다고 주장하지 않는다.
