# meetup-lab-py — 스터디 모임 운영 서비스 (GitHub Copilot 실습용)

스터디 모임을 운영한다. 참석할 사람을 모집하고, 정원이 차면 대기자를 받는다. 참석자는 함께 먹을 메뉴에 투표한다.

- 메뉴 투표: 메뉴 목록 · 투표(1인 1표, 다시 투표하면 덮어쓰기) · 결과 조회
- 행사 신청: 행사 조회 · 신청 · 취소 (지금은 정원 초과 시 `409` 거절 — 대기 등록 · 자동 승격은 이슈 #1)

## 시작하기

```bash
python -m venv .venv      # mac 에서 python 이 없으면 python3 -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   mac/Linux: source .venv/bin/activate
# Windows 에서 '스크립트를 실행할 수 없으므로' 오류가 나면 먼저: Set-ExecutionPolicy -Scope Process Bypass
python -m pip install -r requirements.txt
python scripts/check_env.py
python -m pytest -q
```

Windows ARM 노트북(Snapdragon 등)은 **x64** Python 3.12 를 설치한다. ARM64 Python 에서는 `mcp` 의 의존성(cryptography)이 설치되지 않는다.

## 실행

```bash
# 터미널 ① 서버
python -m uvicorn meetup_lab.app:app --reload
# 터미널 ② 데모 투표 3건 → 피자 2 · 김밥 1 · 샌드위치 0
python scripts/seed_demo.py
# 신청 · 취소 기록 재생 (각 줄의 시각으로 기록)
python scripts/seed_demo.py --replay data/samples/waitlist.log
```

API 문서: http://127.0.0.1:8000/docs (events · polls · registrations)

신청 규칙 확인 (서버 없이 서비스에 직접 재생):

```bash
python scripts/check_registration.py data/samples/waitlist.log
```

## 구조

```text
src/meetup_lab/
  app.py                     create_app() — seed 적재 + 라우터 등록
  models.py                  Event · MenuOption · Vote · Registration · RegistrationEvent
  store.py                   메모리 저장소 (DB 없음)
  api/events.py              GET /events, GET /events/{event_id}
  api/polls.py               GET /events/{event_id}/menu, POST /events/{event_id}/votes, GET /events/{event_id}/votes/results
  api/registrations.py       POST /events/{event_id}/registrations, DELETE /registrations/{registration_id}, GET /events/{event_id}/registrations
  polls/service.py           cast_vote(), results()
  registrations/service.py   RegistrationService.register(), cancel()
  reports/registrations.py   day_range()
  replay_log.py              data/samples/*.log 읽기
data/seed.json               행사 EVT-01 (정원 3) · 메뉴 3개 · 투표 마감 = 앱 시작 + 24시간
data/samples/                basic.log · waitlist.log (한 줄 = 요청 1건)
docs/issues/                 요구사항 (이슈 #1 ~ #3)
scripts/                     check_env.py · seed_demo.py · check_registration.py
tests/                       helpers.py(T0 · at()) · conftest.py(store reset)
```

## 규칙 요약

- 시각은 서버가 기록한 UTC 로 저장하고, 날짜 단위 집계는 KST(Asia/Seoul) 하루 기준이다.
- 투표 마감: `voted_at >= vote_closes_at` 이면 `409` (마감 정각도 거절).
- 저장소는 `store.py` 를 통해서만 읽고 쓴다.
