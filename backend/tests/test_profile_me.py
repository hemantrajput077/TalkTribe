"""
test_profile_me.py — GET /api/v1/profiles/me (PROF-01)

Acceptance criteria tested:
  1. Authenticated user gets HTTP 200 with the correct profile fields.
  2. No token → HTTP 401.
  3. New user with no existing profile row → profile is lazy-created, HTTP 200.
  4. Second call is idempotent — same user_id, no duplicate row.
  5. Response never contains sensitive fields (password, role, account_status).
"""

import pytest

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
