---
name: explain-flow
description: 메뉴 투표 요청이 API 에서 집계까지 어떻게 흐르는지 정해진 4개 파일만 읽고 설명한다. "/explain-flow" 로 직접 실행한다.
disable-model-invocation: true
---
# 메뉴 투표 흐름 설명

아래 **4개 파일만** 읽는다. 다른 파일은 열지 않고, 전체 검색(`#codebase`)도 하지 않는다.

1. `src/meetup_lab/api/polls.py` — API
2. `src/meetup_lab/polls/service.py` — 서비스 (`registrations/service.py` 아님)
3. `src/meetup_lab/models.py` — 모델
4. `src/meetup_lab/store.py` — 저장소

## 출력

1. `POST /events/{event_id}/votes` 부터 `GET /events/{event_id}/votes/results` 의 집계까지 `파일:함수` 순서 목록 (단계마다 한 줄 설명)
2. 1인 1표(다시 투표하면 덮어쓰기)와 투표 마감(`voted_at >= vote_closes_at` → 409)을 어느 함수에서 처리하는지 한 줄씩
3. 흐름에 쓰이는 모델(`Vote`, `PollResults` 등)과 필드

## 규칙
- 코드는 수정하지 않는다.
- 4개 파일에 없는 사실(DB 저장, 없는 함수 이름 등)을 지어내지 않는다.
