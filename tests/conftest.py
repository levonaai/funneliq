"""Shared pytest fixtures."""

from __future__ import annotations

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

import app.auth as auth_module
from app.config import get_settings


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJWKClient:
    def __init__(self, public_key):
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> _FakeSigningKey:
        return _FakeSigningKey(self._public_key)


@pytest.fixture
def make_token(monkeypatch: pytest.MonkeyPatch):
    """Sign ES256 test JWTs verified against a fake JWKS client.

    Mirrors how Supabase actually signs user JWTs (an asymmetric key,
    fetched via a JWKS endpoint - see app/auth.py), without any network
    calls or a real Supabase project.
    """
    monkeypatch.setenv("SUPABASE_URL", "https://test-project.supabase.co")
    get_settings.cache_clear()

    private_key = ec.generate_private_key(ec.SECP256R1())
    monkeypatch.setattr(auth_module, "get_jwks_client", lambda: _FakeJWKClient(private_key.public_key()))

    def _make(**overrides) -> str:
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
            **overrides,
        }
        return jwt.encode(payload, private_key, algorithm="ES256")

    yield _make
    get_settings.cache_clear()
