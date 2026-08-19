"""
JWT utilities for TalkTribe.

- Access tokens  → signed with SECRET_KEY        (HS256, 15 min)
- Refresh tokens → signed with REFRESH_SECRET_KEY (HS256, 7 days)
- Every token carries: sub, email, type, jti (UUID4), iat, exp
- verify_access_token / verify_refresh_token enforce the 'type' claim,
  so a refresh token can never be accepted where an access token is expected.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt

from app.infrastructure.config.config import settings

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


def _build_payload(
    user_id: int,
    email: str,
    token_type: Literal["access", "refresh"],
    expire: datetime,
) -> dict:
    now = datetime.now(UTC)
    return {
        "sub": str(user_id),
        "email": email,
        "type": token_type,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expire,
    }


def _decode(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise EXPIRED_EXCEPTION from None
    except JWTError:
        raise CREDENTIALS_EXCEPTION from None


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = _build_payload(user_id, email, "access", expire)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int, email: str) -> tuple[str, datetime]:
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = _build_payload(user_id, email, "refresh", expire)
    token = jwt.encode(payload, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expire


def verify_access_token(token: str) -> dict:
    payload = _decode(token, settings.SECRET_KEY)
    if payload.get("type") != "access":
        raise CREDENTIALS_EXCEPTION
    return payload


def verify_refresh_token(token: str) -> dict:
    payload = _decode(token, settings.REFRESH_SECRET_KEY)
    if payload.get("type") != "refresh":
        raise CREDENTIALS_EXCEPTION
    return payload


def get_token_jti(token: str, token_type: Literal["access", "refresh"]) -> str:
    secret = settings.SECRET_KEY if token_type == "access" else settings.REFRESH_SECRET_KEY
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        return payload["jti"]
    except JWTError:
        raise CREDENTIALS_EXCEPTION from None


def decode_access_token_unverified_exp(token: str) -> dict:
    """Decode an access token ignoring expiry — used to extract jti/exp for blocklisting."""
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
    except JWTError:
        raise CREDENTIALS_EXCEPTION from None
