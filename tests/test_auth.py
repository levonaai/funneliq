import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_me_without_token_returns_401() -> None:
    response = client.get("/api/me")
    assert response.status_code == 401


def test_me_with_valid_token_returns_user(make_token) -> None:
    token = make_token()
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"user_id": "user-123", "email": "test@example.com"}


def test_me_with_expired_token_returns_401(make_token) -> None:
    token = make_token(exp=int(time.time()) - 10)
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_me_with_wrong_audience_returns_401(make_token) -> None:
    token = make_token(aud="not-authenticated")
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
