"""FastAPI 앱. 실행: `python -m uvicorn meetup_lab.app:app --reload`"""

import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from meetup_lab.api import events, polls, registrations
from meetup_lab.store import store

STATIC_DIR = Path(__file__).parent / "static"

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s %(message)s")


def create_app(now: datetime | None = None) -> FastAPI:
    """저장소를 비우고 data/seed.json 을 적재한 뒤 라우터를 등록한다."""
    store.reset()
    store.load_seed(now=now)

    app = FastAPI(title="meetup-lab", description="스터디 모임 운영 — 메뉴 투표 + 행사 신청·대기자 관리")

    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    def status_page() -> FileResponse:
        """읽기 전용 상태 화면 — 기존 GET API 만 읽는다."""
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    app.include_router(events.router)
    app.include_router(polls.router)
    app.include_router(registrations.router)
    return app


app = create_app()
