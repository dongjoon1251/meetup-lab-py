import pytest
from fastapi.testclient import TestClient
from helpers import T0

from meetup_lab.app import app
from meetup_lab.models import utcnow
from meetup_lab.store import store


@pytest.fixture(autouse=True)
def reset_store():
    """테스트마다 저장소를 비우고 T0 기준으로 seed 를 다시 적재한다."""
    store.reset()
    store.load_seed(now=T0)
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """API 클라이언트. 서버 시각은 T0 로 고정 — 바꾸려면 set_now(at(...))."""
    app.dependency_overrides[utcnow] = lambda: T0
    return TestClient(app)


@pytest.fixture
def set_now():
    def _set(now):
        app.dependency_overrides[utcnow] = lambda: now

    return _set
