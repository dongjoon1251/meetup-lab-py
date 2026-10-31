---
name: api-doc
description: 지정한 FastAPI 라우터의 엔드포인트를 표로 문서화한다. "/api-doc <라우터 파일>" 로 직접 실행한다.
argument-hint: "[src/meetup_lab/api/<파일>.py]"
disable-model-invocation: true
---
# API 문서 만들기

인자로 받은 라우터 파일과 `src/meetup_lab/models.py` **두 파일만** 읽는다.

엔드포인트마다 아래 표 한 줄을 만든다.

| 메서드 · 경로 | 요청(경로·쿼리·바디) | 응답 모델 | 오류 코드 | 예시 `curl` |
|---|---|---|---|---|

## 규칙
- 오류 코드는 코드에 있는 `HTTPException` 과 서비스 예외의 `status_code` 만 적는다(추측 금지).
- 시각 필드는 UTC `Z` 형식 예시를 쓴다.
- `curl` 예시 값은 `data/seed.json` · `data/samples/` 의 실제 값(행사 `EVT-01`, 회원 `M-01`, 메뉴 `MENU-1`, 신청 `REG-1`)을 쓴다.
- 코드는 수정하지 않는다.
