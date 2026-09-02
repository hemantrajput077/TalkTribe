"""
test_auth_identity.py — require_admin guard tests.

get_current_identity and require_authenticated_user are already exercised
by TestMe and TestLogoutAll in test_auth_tokens.py.

This file covers only the new require_admin guard and the two admin-only
endpoints it protects:
  GET    /api/v1/auth/user_data
  DELETE /api/v1/auth/users/{user_id}
"""

import pytest
from sqlalchemy import select, update

from app.domains.auth.domain.enums import UserRole
from app.domains.auth.infrastructure.user_model import User

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
LOGIN_URL = "/api/v1/auth/login"
USER_DATA_URL = "/api/v1/auth/user_data"
DELETE_USER_URL = "/api/v1/auth/users/{user_id}"

_USER = {
    "username": "identityuser",
    "email": "identity@example.com",
    "phone_number": "+919876543211",
    "password": "SecurePass1!",
    "full_name": "Identity User",
}

_ADMIN = {
    "username": "adminuser",
    "email": "admin@example.com",
    "phone_number": "+919876543212",
    "password": "AdminPass1!",
    "full_name": "Admin User",
}


async def _register_verify_login(client, mock_send_email, user: dict) -> dict:
    await client.post(REGISTER_URL, json=user)
    otp = mock_send_email.call_args[0][1]
    await client.post(VERIFY_URL, json={"email": user["email"], "otp": otp})
    resp = await client.post(
        LOGIN_URL, json={"username": user["username"], "password": user["password"]}
    )
    return resp.json()


async def _promote_to_admin(db_session, username: str) -> None:
    await db_session.execute(
        update(User).where(User.username == username).values(role=UserRole.ADMIN)
    )
    await db_session.commit()


class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_user_data_requires_token(self, client):
        resp = await client.get(USER_DATA_URL)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_regular_user_cannot_access_user_data(self, client, mock_send_email):
        tokens = await _register_verify_login(client, mock_send_email, _USER)
        resp = await client.get(
            USER_DATA_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Admin access required."

    @pytest.mark.asyncio
    async def test_admin_user_can_access_user_data(self, client, db_session, mock_send_email):
        tokens = await _register_verify_login(client, mock_send_email, _ADMIN)
        await _promote_to_admin(db_session, _ADMIN["username"])
        resp = await client.get(
            USER_DATA_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_user_requires_token(self, client):
        resp = await client.delete(DELETE_USER_URL.format(user_id=999))
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_user(self, client, mock_send_email):
        tokens = await _register_verify_login(client, mock_send_email, _USER)
        resp = await client.delete(
            DELETE_USER_URL.format(user_id=999),
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Admin access required."

    @pytest.mark.asyncio
    async def test_admin_user_can_delete_user(self, client, db_session, mock_send_email):
        target = {
            "username": "targetuser",
            "email": "target@example.com",
            "phone_number": "+919876543213",
            "password": "SecurePass1!",
            "full_name": "Target User",
        }
        await _register_verify_login(client, mock_send_email, target)
        result = await db_session.execute(select(User).where(User.username == target["username"]))
        target_user = result.scalar_one()

        tokens = await _register_verify_login(client, mock_send_email, _ADMIN)
        await _promote_to_admin(db_session, _ADMIN["username"])

        resp = await client.delete(
            DELETE_USER_URL.format(user_id=target_user.id),
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
