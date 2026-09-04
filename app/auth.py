from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)

# Asymmetric only, deliberately - see get_current_user's docstring for why
# HS256 must never be added here.
ALLOWED_ALGORITHMS = ["ES256", "RS256"]


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    email: str | None
    claims: dict


@lru_cache
def get_jwks_client() -> PyJWKClient:
    settings = get_settings()
    return PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    """Verify a Supabase-issued JWT passed as `Authorization: Bearer <token>`.

    Current Supabase projects sign user JWTs with an asymmetric key (this
    project uses ES256) and publish the public verification key at
    `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` - there is no shared
    secret to verify against locally. `PyJWKClient` fetches and caches that
    key set, matching the right key by the token's `kid` header.

    HS256 is intentionally excluded from `ALLOWED_ALGORITHMS`: mixing it in
    here would open an algorithm-confusion attack, since HS256 treats
    whatever key it's given as a symmetric secret - and the "key" in this
    flow is a *public* key, so anyone could forge a valid-looking HS256
    signature with it if the verifier accepted that algorithm.
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    settings = get_settings()
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server auth is not configured (SUPABASE_URL missing)",
        )

    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=ALLOWED_ALGORITHMS,
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    return CurrentUser(user_id=claims["sub"], email=claims.get("email"), claims=claims)
