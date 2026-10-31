# 행사별 일일 신청 현황 API

## 배경

운영자가 행사별로 하루에 몇 명이 신청·취소했고 몇 명이 승격됐는지 보고 싶어 합니다. 날짜는 운영 기준인 **KST(Asia/Seoul) 하루**로 나눕니다.

```http
GET /reports/registrations?event_id=EVT-01&from=2026-10-01&to=2026-10-31
```

응답 예 (`data/samples/waitlist.log` 재생 후, 이슈 #1 구현 기준):

```json
{"event_id":"EVT-01","days":[{"date":"2026-10-26","registered":5,"cancelled":2,"promoted":1}]}
```

- 관련 코드: `src/meetup_lab/reports/registrations.py` 의 `day_range()` — 날짜 구간 아이디어만 쓰고 집계 로직은 새로 작성

## 인수조건

- [ ] 날짜(KST)별 `registered`(신규 신청) · `cancelled`(취소) · `promoted`(승격) 건수를 돌려준다.
- [ ] 현재 상태가 아니라 이력(`RegistrationEvent`)으로 집계한다 — 취소된 신청도 최초 신청일의 신규 1건에 포함한다.
- [ ] `from` · `to` 는 양 끝 날짜를 포함한다.
- [ ] 없는 행사는 404 를 돌려준다.
- [ ] `from > to` 는 422 를 돌려준다.
