"""
test_jwt.py — JWT utility unit tests.

Tests the JWT create/verify cycle in isolation — no database required.
Uses the SECRET_KEY and REFRESH_SECRET_KEY from conftest env overrides.
"""

from datetime import UTC

import pytest


class TestAccessToken:
    """Tests for access token creation and verification."""

    def test_create_and_verify_access_token(self):
        from app.infrastructure.security.jwt import create_access_token, verify_access_token

        token = create_access_token(user_id=42, email="user@example.com")
        assert isinstance(token, str)
        assert len(token) > 0

        payload = verify_access_token(token)
        assert payload["sub"] == "42"
        assert payload["email"] == "user@example.com"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_access_token_rejected_as_refresh(self):
        """An access token must NOT be accepted by verify_refresh_token."""
        from fastapi import HTTPException

        from app.infrastructure.security.jwt import create_access_token, verify_refresh_token

        token = create_access_token(user_id=1, email="u@e.com")
        with pytest.raises(HTTPException) as exc_info:
            verify_refresh_token(token)
        assert exc_info.value.status_code == 401


class TestRefreshToken:
    """Tests for refresh token creation and verification."""

    def test_create_and_verify_refresh_token(self):
        from app.infrastructure.security.jwt import create_refresh_token, verify_refresh_token

        token, expires_at = create_refresh_token(user_id=99, email="user@example.com")
        assert isinstance(token, str)

        payload = verify_refresh_token(token)
        assert payload["sub"] == "99"
        assert payload["type"] == "refresh"

    def test_refresh_token_rejected_as_access(self):
        """A refresh token must NOT be accepted by verify_access_token."""
        from fastapi import HTTPException

        from app.infrastructure.security.jwt import create_refresh_token, verify_access_token

        token, _ = create_refresh_token(user_id=1, email="u@e.com")
        with pytest.raises(HTTPException) as exc_info:
            verify_access_token(token)
        assert exc_info.value.status_code == 401

    def test_refresh_token_returns_expiry_datetime(self):
        from datetime import datetime

        from app.infrastructure.security.jwt import create_refresh_token

        _, expires_at = create_refresh_token(user_id=5, email="u@e.com")
        assert isinstance(expires_at, datetime)
        assert expires_at > datetime.now(UTC)


class TestGetTokenJti:
    """Tests for JTI extraction."""

    def test_get_jti_from_access_token(self):
        from app.infrastructure.security.jwt import create_access_token, get_token_jti

        token = create_access_token(user_id=7, email="u@e.com")
        jti = get_token_jti(token, "access")
        assert isinstance(jti, str)
        assert len(jti) == 36  # UUID4 format

    def test_get_jti_from_refresh_token(self):
        from app.infrastructure.security.jwt import create_refresh_token, get_token_jti

        token, _ = create_refresh_token(user_id=8, email="u@e.com")
        jti = get_token_jti(token, "refresh")
        assert isinstance(jti, str)
        assert len(jti) == 36
