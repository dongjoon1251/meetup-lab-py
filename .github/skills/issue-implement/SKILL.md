---
name: issue-implement
description: 지정한 GitHub 이슈를 읽고 테스트와 최소 구현으로 해결한다.
disable-model-invocation: true
---
1. 입력 이슈 번호로 GitHub MCP에서 실제 본문과 인수조건을 읽는다. 문서와 대조한다.
2. 현재 브랜치·변경 사항을 확인하고 기존 작업을 보존한다. 섹션 7은 feat/issue-2에서 feat/issue-<실제 번호>를 만든다.
3. 인수조건을 테스트로 옮기고 최소 구현한다. 웹훅은 최대 3회 시도, 미설정 시 생략, 실패 시 상태 유지, 중복 알림 금지다.
4. 외부 HTTP를 모의하고 python -m pytest -q를 Asia/Seoul·UTC에서 실행한다. 섹션 7 완료 시 모두 통과해야 한다.
5. 승인된 커밋 범위에서만 feat: … (#<번호>) 커밋을 만든다. 실제 diff·테스트 결과를 보고한다.
push·PR은 /pr-create에서 별도로 승인받는다. 이슈를 임의로 닫거나 PR을 merge하지 않는다.
