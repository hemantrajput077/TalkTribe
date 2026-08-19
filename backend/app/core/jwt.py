"""
Production-grade JWT utilities for TalkTribe.

Design decisions:
  - Access tokens are signed with SECRET_KEY        (HS256, 15 min)
  - Refresh tokens are signed with REFRESH_SECRET_KEY (HS256, 7 days)
  - Every token carries: sub (user_id), email, type, jti (unique id), iat
  - verify_access_token / verify_refresh_token enforce the 'type' claim so
    a refresh token can NEVER be used as an access token and vice-versa.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings

# ── Credential exception reused everywhere ──────────────────────────────────
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)

EXPIRED_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token has expired.",
    headers={"WWW-Authenticate": "Bearer"},
)


# ── Internal helpers ────────────────────────────────────────────────────────


def _build_payload(
    user_id: int,
    email: str,
    token_type: Literal["access", "refresh"],
    expire: datetime,
) -> dict:
    now = datetime.now(UTC)
    return {
        "sub": str(user_id),  # subject  – always a string
        "email": email,
        "type": token_type,
        "jti": str(uuid.uuid4()),  # unique token ID (for revocation)
        "iat": now,  # issued-at
        "exp": expire,  # expiry
    }


def _decode(token: str, secret: str) -> dict:
    """Raw decode; raises HTTPException on failure."""
    try:
        return jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise EXPIRED_EXCEPTION from None
    except JWTError:
        raise CREDENTIALS_EXCEPTION from None


# ── Public API ───────────────────────────────────────────────────────────────


def create_access_token(user_id: int, email: str) -> str:
    """Return a signed access JWT (short-lived)."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = _build_payload(user_id, email, "access", expire)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int, email: str) -> tuple[str, datetime]:
    """
    Return (signed refresh JWT, expiry datetime).
    The expiry is returned so it can be persisted to the DB.
    Refresh tokens use a *different* secret key than access tokens.
    """
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = _build_payload(user_id, email, "refresh", expire)
    token = jwt.encode(payload, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expire


def verify_access_token(token: str) -> dict:
    """
    Decode & validate an access token.
    Raises HTTP 401 if invalid, expired, or wrong type.
    """
    payload = _decode(token, settings.SECRET_KEY)
    if payload.get("type") != "access":
        raise CREDENTIALS_EXCEPTION
    return payload


def verify_refresh_token(token: str) -> dict:
    """
    Decode & validate a refresh token.
    Raises HTTP 401 if invalid, expired, or wrong type.
    """
    payload = _decode(token, settings.REFRESH_SECRET_KEY)
    if payload.get("type") != "refresh":
        raise CREDENTIALS_EXCEPTION
    return payload


def get_token_jti(token: str, token_type: Literal["access", "refresh"]) -> str:
    """Extract the jti from a token without strict validation (use carefully)."""
    secret = settings.SECRET_KEY if token_type == "access" else settings.REFRESH_SECRET_KEY  # nosec B105
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},  # allow expired for revocation lookup
        )
        return payload["jti"]
    except JWTError:
        raise CREDENTIALS_EXCEPTION from None
