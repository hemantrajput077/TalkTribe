"""
test_auth_tokens.py — Token lifecycle and protected route tests.

Covers:
  POST /api/v1/auth/refresh
  POST /api/v1/auth/logout
  POST /api/v1/auth/logout-all
  GET  /api/v1/auth/me
"""

import pytest
from sqlalchemy import update

from app.domains.auth.domain.enums import AccountStatus
from app.domains.auth.infrastructure.user_model import User

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
LOGOUT_ALL_URL = "/api/v1/auth/logout-all"
ME_URL = "/api/v1/auth/me"

_USER = {
    "username": "tokenuser",
    "email": "token@example.com",
    "phone_number": "+919876543210",
    "password": "SecurePass1!",
    "full_name": "Token User",
}


async def _get_tokens(client, mock_send_email, user=None):
    """Register, verify, and login — returns the token pair dict."""
    user = user or _USER
    await client.post(REGISTER_URL, json=user)
    otp = mock_send_email.call_args[0][1]
    await client.post(VERIFY_URL, json={"email": user["email"], "otp": otp})
    response = await client.post(
        LOGIN_URL,
        json={
            "username": user["username"],
            "password": user["password"],
        },
    )
    return response.json()  # {"access_token": ..., "refresh_token": ..., "token_type": ...}


# ── /me ───────────────────────────────────────────────────────────────────────


class TestMe:
    @pytest.mark.asyncio
    async def test_me_returns_200(self, client, mock_send_email):
        tokens = await _get_tokens(client, mock_send_email)
        response = await client.get(
            ME_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_me_returns_correct_username(self, client, mock_send_email):
        tokens = await _get_tokens(client, mock_send_email)
        response = await client.get(
            ME_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert response.json()["username"] == _USER["username"]

    @pytest.mark.asyncio
    async def test_me_returns_phone_number(self, client, mock_send_email):
        tokens = await _get_tokens(client, mock_send_email)
        response = await client.get(
            ME_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert response.json()["phone_number"] == _USER["phone_number"]

    @pytest.mark.asyncio
    async def test_me_without_token_returns_401(self, client):
        response = await client.get(ME_URL)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_invalid_token_returns_401(self, client):
        response = await client.get(ME_URL, headers={"Authorization": "Bearer notavalidtoken"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_returns_role_and_account_status(self, client, mock_send_email):
        tokens = await _get_tokens(client, mock_send_email)
        response = await client.get(
            ME_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        data = response.json()
        assert data["role"] == "USER"
        assert data["account_status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_suspended_user_cannot_access_protected_route(
        self, client, db_session, mock_send_email
    ):
        tokens = await _get_tokens(client, mock_send_email)
        await db_session.execute(
            update(User)
            .where(User.username == _USER["username"])
            .values(account_status=AccountStatus.SUSPENDED)
        )
        await db_session.commit()
        response = await client.get(
            ME_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "ACCOUNT_SUSPENDED"

    @pytest.mark.asyncio
    async def test_blocked_user_cannot_access_protected_route(
        self, client, db_session, mock_send_email
    ):
        tokens = await _get_tokens(client, mock_send_email)
        await db_session.execute(
            update(User)
            .where(User.username == _USER["username"])
            .values(account_status=AccountStatus.BLOCKED)
        )
        await db_session.commit()
        response = await client.get(
            ME_URL, headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "ACCOUNT_BLOCKED"


# ── /refresh ──────────────────────────────────────────────────────────────────


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_returns_200(self, client, mock_send_email):
        tokens = await _get_tokens(client, mock_send_email)
        response = await client.post(
            REFRESH_URL,
            json={
                "refresh_token": tokens["refresh_token"],
                "access_token": tokens["access_token"],
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_refresh_returns_new_token_pair(self, client, mock_send_email):
        tokens = await _get_tokens(client, mock_send_email)
        response = await client.post(
            REFRESH_URL,
            json={
                "refresh_token": tokens["refresh_token"],
                "access_token": tokens["access_token"],
            },
        )
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

    @pytest.mark.asyncio
    async def test_refresh_with_garbage_token_returns_401(self, client, mock_send_email):
        await _get_tokens(client, mock_send_email)
        response = await client.post(
            REFRESH_URL,
            json={
                "refresh_token": "not.a.real.token",
                "access_token": "not.a.real.token",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_in_refresh_field_returns_401(
        self, client, mock_send_email
    ):
        """An access token must NOT be accepted as a refresh token."""
        tokens = await _get_tokens(client, mock_send_email)
        response = await client.post(
            REFRESH_URL,
            json={
                "refresh_token": tokens["access_token"],  # wrong token type
                "access_token": tokens["access_token"],
            },
        )
        assert response.status_code == 401


# ── /logout ───────────────────────────────────────────────────────────────────


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_returns_204(self, client, mock_send_email):
        tokens = await _get_tokens(client, mock_send_email)
        response = await client.post(
            LOGOUT_URL,
            json={
                "refresh_token": tokens["refresh_token"],
                "access_token": tokens["access_token"],
            },
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_logout_response_has_no_body(self, client, mock_send_email):
        tokens = await _get_tokens(client, mock_send_email)
        response = await client.post(
            LOGOUT_URL,
            json={
                "refresh_token": tokens["refresh_token"],
                "access_token": tokens["access_token"],
            },
        )
        assert response.content == b""

    @pytest.mark.asyncio
    async def test_refresh_token_is_revoked_after_logout(self, client, mock_send_email):
        tokens = await _get_tokens(client, mock_send_email)
        await client.post(
            LOGOUT_URL,
            json={
                "refresh_token": tokens["refresh_token"],
                "access_token": tokens["access_token"],
            },
        )
        # Attempting to refresh with the now-revoked token must fail
        response = await client.post(
            REFRESH_URL,
            json={
                "refresh_token": tokens["refresh_token"],
                "access_token": tokens["access_token"],
            },
        )
        assert response.status_code == 401


# ── /logout-all ───────────────────────────────────────────────────────────────


class TestLogoutAll:
    @pytest.mark.asyncio
    async def test_logout_all_returns_204(self, client, mock_send_email):
        tokens = await _get_tokens(client, mock_send_email)
        response = await client.post(
            LOGOUT_ALL_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_logout_all_without_token_returns_401(self, client):
        response = await client.post(LOGOUT_ALL_URL)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_all_refresh_tokens_revoked_after_logout_all(self, client, mock_send_email):
        # Login twice — two separate refresh tokens in DB
        tokens_a = await _get_tokens(client, mock_send_email)

        # Second login for the same user
        login_b = await client.post(
            LOGIN_URL,
            json={
                "username": _USER["username"],
                "password": _USER["password"],
            },
        )
        tokens_b = login_b.json()

        # Logout-all using first session's access token
        await client.post(
            LOGOUT_ALL_URL,
            headers={"Authorization": f"Bearer {tokens_a['access_token']}"},
        )

        # Both refresh tokens should now be revoked
        resp_a = await client.post(
            REFRESH_URL,
            json={
                "refresh_token": tokens_a["refresh_token"],
                "access_token": tokens_a["access_token"],
            },
        )
        resp_b = await client.post(
            REFRESH_URL,
            json={
                "refresh_token": tokens_b["refresh_token"],
                "access_token": tokens_b["access_token"],
            },
        )
        assert resp_a.status_code == 401
        assert resp_b.status_code == 401
