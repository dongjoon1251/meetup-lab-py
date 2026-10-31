# 대기 등록과 자동 승격

## 배경

행사 `EVT-01` 은 정원이 3명입니다. 지금은 정원이 차면 신청을 `409 정원 초과` 로 거절해서, 참가자가 취소해도 빈자리를 채울 방법이 없습니다.
정원이 차면 신청자를 대기자로 등록하고, 참가자가 취소하면 가장 먼저 신청한 대기자 한 명을 참가자로 승격합니다.

- 관련 코드: `src/meetup_lab/registrations/service.py` (`RegistrationService.register()`, `cancel()`)
- 확인 데이터: `data/samples/waitlist.log` — 정원 3에 `M-01`~`M-05` 신청 → `M-03` 취소 → 같은 취소 재요청 → `M-05` 취소
- 확인 명령: `python scripts/check_registration.py data/samples/waitlist.log`

## 인수조건

- [ ] 정원 미만이면 `CONFIRMED`, 정원이 차면 `WAITLISTED` 로 등록한다.
- [ ] 같은 행사에 같은 참가자가 중복 신청할 수 없다(409).
- [ ] 참가자 취소 시 대기 순서(`seq`)가 가장 빠른 **한 명만** 승격한다.
- [ ] 대기자가 취소하면 다른 대기자를 승격하지 않는다.
- [ ] 이미 취소한 신청을 다시 취소해도 추가 승격하지 않는다.
- [ ] 다른 행사의 신청 상태에 영향을 주지 않는다.

## 기대 결과 (`waitlist.log`)

- `M-04`·`M-05` 가 `WAITLISTED`(seq 4·5)로 등록된다.
- `M-03` 취소 때 `M-04` 한 명만 `CONFIRMED` 로 승격된다.
- 같은 취소 재요청 뒤에 추가 승격이 없다.
- 대기자 `M-05` 취소 때 승격이 없다.
- 최종: `M-01`·`M-02`·`M-04` `CONFIRMED`, `M-03`·`M-05` `CANCELLED`, 대기 0명.
- 상태 변경은 `RegistrationEvent` 이력(`WAITLISTED` · `CANCELLED` · `PROMOTED`)으로도 남긴다 — 이슈 #2 집계의 근거.
