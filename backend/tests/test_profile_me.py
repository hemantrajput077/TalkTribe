"""
test_profile_me.py — GET /api/v1/profiles/me (PROF-01)

Acceptance criteria tested:
  1. Authenticated user gets HTTP 200 with the correct profile fields.
  2. No token → HTTP 401.
  3. New user with no existing profile row → profile is lazy-created, HTTP 200.
  4. Second call is idempotent — same user_id, no duplicate row.
  5. Response never contains sensitive fields (password, role, account_status).

Service-layer unit tests (mocked repository):
  6. Profile already exists → returned directly, no INSERT attempted.
  7. IntegrityError + profile found on re-fetch → concurrent creation recovered.
  8. IntegrityError + profile None on re-fetch → FK violation → HTTP 404.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.domains.profile.application.profile_service import ProfileService
from app.domains.profile.infrastructure.profile_model import Profile

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
LOGIN_URL = "/api/v1/auth/login"
PROFILE_ME_URL = "/api/v1/profiles/me"

_USER = {
    "username": "profileuser",
    "email": "profile@example.com",
    "phone_number": "+919876543220",
    "password": "SecurePass1!",
    "full_name": "Profile User",
}


async def _register_verify_login(client, mock_send_email, user: dict) -> str:
    """Register → verify email → login. Returns the access token."""
    await client.post(REGISTER_URL, json=user)
    otp = mock_send_email.call_args[0][1]
    await client.post(VERIFY_URL, json={"email": user["email"], "otp": otp})
    resp = await client.post(
        LOGIN_URL, json={"username": user["username"], "password": user["password"]}
    )
    return resp.json()["access_token"]


class TestProfileMe:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client):
        resp = await client.get(PROFILE_ME_URL)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticated_user_gets_200(self, client, mock_send_email):
        token = await _register_verify_login(client, mock_send_email, _USER)
        resp = await client.get(PROFILE_ME_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_new_user_profile_lazy_created_with_null_fields(self, client, mock_send_email):
        token = await _register_verify_login(client, mock_send_email, _USER)
        resp = await client.get(PROFILE_ME_URL, headers={"Authorization": f"Bearer {token}"})
        data = resp.json()
        assert data["bio"] is None
        assert data["profession"] is None
        assert data["location"] is None
        assert data["avatar_url"] is None
        assert "user_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_second_call_returns_same_profile(self, client, mock_send_email):
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}
        first = await client.get(PROFILE_ME_URL, headers=headers)
        second = await client.get(PROFILE_ME_URL, headers=headers)
        assert first.json()["user_id"] == second.json()["user_id"]
        assert first.json()["created_at"] == second.json()["created_at"]

    @pytest.mark.asyncio
    async def test_response_excludes_sensitive_fields(self, client, mock_send_email):
        token = await _register_verify_login(client, mock_send_email, _USER)
        resp = await client.get(PROFILE_ME_URL, headers={"Authorization": f"Bearer {token}"})
        data = resp.json()
        for field in ("password", "password_hash", "role", "account_status", "otp"):
            assert field not in data, (
                f"Sensitive field '{field}' must not appear in profile response"
            )


class TestProfileServiceUnit:
    """
    Unit tests for ProfileService.get_or_create_profile.
    These bypass the HTTP stack and mock the repository directly so we can
    simulate IntegrityError paths that cannot be triggered through a real DB in tests.
    """

    @pytest.mark.asyncio
    async def test_existing_profile_returned_directly(self):
        mock_db = AsyncMock()
        existing = Profile(user_id=1)

        svc = ProfileService(mock_db)
        svc.repo = AsyncMock()
        svc.repo.get_by_user_id.return_value = existing

        result = await svc.get_or_create_profile(1)

        assert result is existing
        svc.repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_new_profile_created_when_none_exists(self):
        mock_db = AsyncMock()
        created = Profile(user_id=1)

        svc = ProfileService(mock_db)
        svc.repo = AsyncMock()
        svc.repo.get_by_user_id.return_value = None
        svc.repo.create.return_value = created

        result = await svc.get_or_create_profile(1)

        assert result is created
        svc.repo.create.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_integrity_error_concurrent_creation_recovers(self):
        """
        Simulates: two requests race, both see no profile, both try INSERT.
        The second one hits IntegrityError (UNIQUE), rolls back, re-fetches
        the row the first request committed — and returns it successfully.
        """
        mock_db = AsyncMock()
        recovered = Profile(user_id=1)

        svc = ProfileService(mock_db)
        svc.repo = AsyncMock()
        # First call (pre-create check) → None; second call (post-rollback) → found
        svc.repo.get_by_user_id.side_effect = [None, recovered]
        svc.repo.create.side_effect = IntegrityError(None, None, Exception("unique violation"))

        result = await svc.get_or_create_profile(1)

        assert result is recovered
        mock_db.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_integrity_error_fk_violation_raises_404(self):
        """
        Simulates: user is deleted between auth check and INSERT.
        IntegrityError is caught, rollback runs, but re-fetch returns None
        because no profile was ever created. Expects HTTP 404.
        """
        mock_db = AsyncMock()

        svc = ProfileService(mock_db)
        svc.repo = AsyncMock()
        svc.repo.get_by_user_id.return_value = None  # None on both calls
        svc.repo.create.side_effect = IntegrityError(None, None, Exception("fk violation"))

        with pytest.raises(HTTPException) as exc_info:
            await svc.get_or_create_profile(1)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "USER_NOT_FOUND"
        mock_db.rollback.assert_awaited_once()
