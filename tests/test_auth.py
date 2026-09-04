import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

TEST_SECRET = "test-secret-that-is-long-enough-for-hs256"

client = TestClient(app)


@pytest.fixture(autouse=True)
def _configure_test_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _make_token(**overrides) -> str:
    payload = {
        "sub": "user-123",
        "email": "test@example.com",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        **overrides,
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


def test_me_without_token_returns_401() -> None:
    response = client.get("/api/me")
    assert response.status_code == 401


def test_me_with_valid_token_returns_user() -> None:
    token = _make_token()
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"user_id": "user-123", "email": "test@example.com"}


def test_me_with_expired_token_returns_401() -> None:
    token = _make_token(exp=int(time.time()) - 10)
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_me_with_wrong_audience_returns_401() -> None:
    token = _make_token(aud="not-authenticated")
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
