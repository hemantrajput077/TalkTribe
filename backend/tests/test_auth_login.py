"""
test_auth_login.py — Login endpoint tests.

Covers:
  POST /api/v1/auth/login
"""

import pytest
from sqlalchemy import update

from app.domains.auth.domain.enums import AccountStatus
from app.domains.auth.infrastructure.user_model import User

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
LOGIN_URL = "/api/v1/auth/login"

_USER = {
    "username": "loginuser",
    "email": "login@example.com",
    "phone_number": "+919876543210",
    "password": "SecurePass1!",
}


async def _setup_verified_user(client, mock_send_email, user=None):
    """Register and verify a user. Returns the user dict."""
    user = user or _USER
    await client.post(REGISTER_URL, json=user)
    otp = mock_send_email.call_args[0][1]
    await client.post(VERIFY_URL, json={"email": user["email"], "otp": otp})
    return user


class TestLoginSuccess:
    @pytest.mark.asyncio
    async def test_returns_200(self, client, mock_send_email):
        await _setup_verified_user(client, mock_send_email)
        response = await client.post(
            LOGIN_URL,
            json={
                "username": _USER["username"],
                "password": _USER["password"],
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_access_and_refresh_tokens(self, client, mock_send_email):
        await _setup_verified_user(client, mock_send_email)
        response = await client.post(
            LOGIN_URL,
            json={
                "username": _USER["username"],
                "password": _USER["password"],
            },
        )
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_tokens_are_non_empty_strings(self, client, mock_send_email):
        await _setup_verified_user(client, mock_send_email)
        response = await client.post(
            LOGIN_URL,
            json={
                "username": _USER["username"],
                "password": _USER["password"],
            },
        )
        data = response.json()
        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 10
        assert isinstance(data["refresh_token"], str) and len(data["refresh_token"]) > 10

    @pytest.mark.asyncio
    async def test_token_type_is_bearer(self, client, mock_send_email):
        await _setup_verified_user(client, mock_send_email)
        response = await client.post(
            LOGIN_URL,
            json={
                "username": _USER["username"],
                "password": _USER["password"],
            },
        )
        assert response.json()["token_type"] == "Bearer"


class TestLoginFailures:
    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self, client, mock_send_email):
        await _setup_verified_user(client, mock_send_email)
        response = await client.post(
            LOGIN_URL,
            json={
                "username": _USER["username"],
                "password": "WrongPass1!",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_username_returns_401(self, client, mock_send_email):
        await _setup_verified_user(client, mock_send_email)
        response = await client.post(
            LOGIN_URL,
            json={
                "username": "ghostuser",
                "password": _USER["password"],
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unverified_user_returns_403(self, client, mock_send_email):
        # Register but do NOT verify
        await client.post(REGISTER_URL, json=_USER)
        response = await client.post(
            LOGIN_URL,
            json={
                "username": _USER["username"],
                "password": _USER["password"],
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_error_message_does_not_reveal_which_field_is_wrong(
        self, client, mock_send_email
    ):
        """Username and wrong-password errors must return the same message (timing-safe)."""
        await _setup_verified_user(client, mock_send_email)
        wrong_user_resp = await client.post(
            LOGIN_URL,
            json={
                "username": "ghostuser",
                "password": _USER["password"],
            },
        )
        wrong_pass_resp = await client.post(
            LOGIN_URL,
            json={
                "username": _USER["username"],
                "password": "WrongPass1!",
            },
        )
        assert wrong_user_resp.json()["detail"] == wrong_pass_resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_suspended_user_returns_403(self, client, db_session, mock_send_email):
        await _setup_verified_user(client, mock_send_email)
        await db_session.execute(
            update(User)
            .where(User.username == _USER["username"])
            .values(account_status=AccountStatus.SUSPENDED)
        )
        await db_session.commit()
        response = await client.post(
            LOGIN_URL, json={"username": _USER["username"], "password": _USER["password"]}
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "ACCOUNT_SUSPENDED"

    @pytest.mark.asyncio
    async def test_blocked_user_returns_403(self, client, db_session, mock_send_email):
        await _setup_verified_user(client, mock_send_email)
        await db_session.execute(
            update(User)
            .where(User.username == _USER["username"])
            .values(account_status=AccountStatus.BLOCKED)
        )
        await db_session.commit()
        response = await client.post(
            LOGIN_URL, json={"username": _USER["username"], "password": _USER["password"]}
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "ACCOUNT_BLOCKED"

    @pytest.mark.asyncio
    async def test_deleted_user_returns_403(self, client, db_session, mock_send_email):
        await _setup_verified_user(client, mock_send_email)
        await db_session.execute(
            update(User)
            .where(User.username == _USER["username"])
            .values(account_status=AccountStatus.DELETED)
        )
        await db_session.commit()
        response = await client.post(
            LOGIN_URL, json={"username": _USER["username"], "password": _USER["password"]}
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "ACCOUNT_DELETED"
