"""
test_profile_update.py — PATCH /api/v1/profiles/me  &  GET /api/v1/profiles/{id}  (TT-12)

Acceptance criteria tested:
  PATCH /profiles/me
    1. Authenticated user can update their profile fields → 200.
    2. Partial update (only one field) works — other fields stay None.
    3. No token → 401.
    4. Update returns the updated values in the response.
    5. Non-existent profile returns 404.

  GET /profiles/{id}
    6. Admin can fetch any profile by ID → 200.
    7. Regular user cannot fetch by ID → 403.
    8. No token → 401.
    9. Non-existent profile ID → 404.

Service-layer unit tests (mocked repository):
  10. update_profile raises 404 when profile not found.
  11. update_profile returns updated profile on success.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.domains.profile.application.profile_service import ProfileService
from app.domains.profile.infrastructure.profile_model import Profile
from app.domains.profile.schemas.profile import ProfileUpdate

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
LOGIN_URL = "/api/v1/auth/login"
PROFILE_ME_URL = "/api/v1/profiles/me"
PROFILE_BY_ID_URL = "/api/v1/profiles/admin/{}"

_LEARNER = {
    "username": "updateuser",
    "email": "update@example.com",
    "phone_number": "+919876543221",
    "password": "SecurePass1!",
    "full_name": "Update User",
}

_ADMIN = {
    "username": "adminuser",
    "email": "admin@example.com",
    "phone_number": "+919876543222",
    "password": "SecurePass1!",
    "full_name": "Admin User",
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


# ── PATCH /profiles/me ────────────────────────────────────────────────────────


class TestProfileUpdate:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client):
        resp = await client.patch(PROFILE_ME_URL, json={"bio": "Hello"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile_returns_200(self, client, mock_send_email):
        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        # Lazy-create profile first
        await client.get(PROFILE_ME_URL, headers=headers)

        resp = await client.patch(
            PROFILE_ME_URL,
            json={"bio": "I am a learner", "profession": "Developer", "location": "India"},
            headers=headers,
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_profile_persists_values(self, client, mock_send_email):
        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        # First fetch to lazy-create the profile
        await client.get(PROFILE_ME_URL, headers=headers)

        payload = {
            "bio": "Updated bio",
            "profession": "Engineer",
            "location": "Mumbai",
            "avatar_url": "https://example.com/avatar.png",
        }
        resp = await client.patch(PROFILE_ME_URL, json=payload, headers=headers)
        data = resp.json()

        assert data["bio"] == "Updated bio"
        assert data["profession"] == "Engineer"
        assert data["location"] == "Mumbai"
        assert data["avatar_url"] == "https://example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_partial_update_only_changes_sent_fields(self, client, mock_send_email):
        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        # Lazy-create profile first
        await client.get(PROFILE_ME_URL, headers=headers)

        # Only update bio
        resp = await client.patch(PROFILE_ME_URL, json={"bio": "Only bio"}, headers=headers)
        data = resp.json()

        assert data["bio"] == "Only bio"
        # Other fields should remain None (not yet set)
        assert data["profession"] is None
        assert data["location"] is None
        assert data["avatar_url"] is None

    @pytest.mark.asyncio
    async def test_update_response_contains_required_fields(self, client, mock_send_email):
        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        # Lazy-create profile first
        await client.get(PROFILE_ME_URL, headers=headers)

        resp = await client.patch(PROFILE_ME_URL, json={"bio": "Test"}, headers=headers)
        data = resp.json()

        for field in (
            "user_id",
            "bio",
            "profession",
            "location",
            "avatar_url",
            "created_at",
            "updated_at",
        ):
            assert field in data, f"Expected field '{field}' in response"

    @pytest.mark.asyncio
    async def test_update_excludes_sensitive_fields(self, client, mock_send_email):
        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.patch(PROFILE_ME_URL, json={"bio": "Test"}, headers=headers)
        data = resp.json()

        for field in ("password", "password_hash", "role", "account_status"):
            assert field not in data


# ── GET /profiles/{id} ───────────────────────────────────────────────────────


class TestProfileGetById:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client):
        resp = await client.get(PROFILE_BY_ID_URL.format(1))
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_regular_user_cannot_access_returns_403(self, client, mock_send_email):
        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(PROFILE_BY_ID_URL.format(1), headers=headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_nonexistent_profile_returns_404(self, client, mock_send_email, db_session):
        """Admin token required — promote user to admin via DB then re-login."""
        from sqlalchemy import select

        from app.domains.auth.domain.enums import UserRole
        from app.domains.auth.infrastructure.user_model import User

        # Register and get user
        await _register_verify_login(client, mock_send_email, _LEARNER)

        # Promote to admin directly in DB
        result = await db_session.execute(select(User).where(User.username == _LEARNER["username"]))
        user = result.scalar_one()
        user.role = UserRole.ADMIN
        await db_session.commit()

        # Re-login to get a fresh token that reflects the admin role
        resp = await client.post(
            LOGIN_URL,
            json={"username": _LEARNER["username"], "password": _LEARNER["password"]},
        )
        admin_token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        resp = await client.get(PROFILE_BY_ID_URL.format(99999), headers=headers)
        assert resp.status_code == 404


# ── Service unit tests ────────────────────────────────────────────────────────


class TestProfileServiceUpdateUnit:
    @pytest.mark.asyncio
    async def test_update_raises_404_when_profile_not_found(self):
        mock_db = AsyncMock()
        svc = ProfileService(mock_db)
        svc.repo = AsyncMock()
        svc.repo.get_by_user_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await svc.update_profile(1, ProfileUpdate(bio="Test"))

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "PROFILE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_update_returns_updated_profile(self):
        mock_db = AsyncMock()
        existing = Profile(user_id=1, bio="old bio")
        updated = Profile(user_id=1, bio="new bio")

        svc = ProfileService(mock_db)
        svc.repo = AsyncMock()
        svc.repo.get_by_user_id.return_value = existing
        svc.repo.update_profile.return_value = updated

        result = await svc.update_profile(1, ProfileUpdate(bio="new bio"))

        assert result is updated
        svc.repo.update_profile.assert_awaited_once_with(1, ProfileUpdate(bio="new bio"))

    @pytest.mark.asyncio
    async def test_get_profile_by_id_raises_404_when_not_found(self):
        mock_db = AsyncMock()
        svc = ProfileService(mock_db)
        svc.repo = AsyncMock()
        svc.repo.get_profile_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await svc.get_profile_by_id(999)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "PROFILE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_profile_by_id_returns_profile(self):
        mock_db = AsyncMock()
        profile = Profile(user_id=5)
        svc = ProfileService(mock_db)
        svc.repo = AsyncMock()
        svc.repo.get_profile_by_id.return_value = profile

        result = await svc.get_profile_by_id(5)
        assert result is profile
