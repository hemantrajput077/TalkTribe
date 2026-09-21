"""
test_peer_profile.py — GET /api/v1/profiles/{user_id} (BUG-02)

Acceptance criteria tested:
  1. ACTIVE account returns 200 with profile data.
  2. SUSPENDED account returns 404.
  3. BLOCKED account returns 404.
  4. DELETED account returns 404.
  5. 404 response body does not contain "suspended", "blocked", or "deleted".
  6. Non-existent user_id returns 404.
  7. Unauthenticated request returns 401.
"""

import pytest
from sqlalchemy import update

from app.domains.auth.domain.enums import AccountStatus
from app.domains.auth.infrastructure.user_model import User

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
LOGIN_URL = "/api/v1/auth/login"
PROFILES_URL = "/api/v1/profiles"

_VIEWER = {
    "username": "vieweruser",
    "email": "viewer@example.com",
    "phone_number": "+919000000001",
    "password": "SecurePass1!",
    "full_name": "Viewer User",
}

_TARGET = {
    "username": "targetuser",
    "email": "target@example.com",
    "phone_number": "+919000000002",
    "password": "SecurePass1!",
    "full_name": "Target User",
}


async def _register_verify_login(client, mock_send_email, user: dict) -> tuple[str, int]:
    """Register → verify email → login. Returns (access_token, user_id)."""
    await client.post(REGISTER_URL, json=user)
    otp = mock_send_email.call_args[0][1]
    await client.post(VERIFY_URL, json={"email": user["email"], "otp": otp})
    resp = await client.post(
        LOGIN_URL, json={"username": user["username"], "password": user["password"]}
    )
    token = resp.json()["access_token"]

    # Fetch user_id via /auth/me
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]


async def _seed_profile(client, token: str) -> None:
    """Touch GET /profiles/me to lazy-create the profile row."""
    await client.get(f"{PROFILES_URL}/me", headers={"Authorization": f"Bearer {token}"})


async def _set_account_status(db_session, user_id: int, status: AccountStatus) -> None:
    await db_session.execute(update(User).where(User.id == user_id).values(account_status=status))
    await db_session.commit()


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestPeerProfileAccountStatus:
    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, client):
        resp = await client.get(f"{PROFILES_URL}/999")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_active_account_returns_200(self, client, mock_send_email, db_session):
        viewer_token, _ = await _register_verify_login(client, mock_send_email, _VIEWER)
        target_token, target_id = await _register_verify_login(client, mock_send_email, _TARGET)
        await _seed_profile(client, target_token)

        resp = await client.get(
            f"{PROFILES_URL}/{target_id}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_suspended_account_returns_404(self, client, mock_send_email, db_session):
        viewer_token, _ = await _register_verify_login(client, mock_send_email, _VIEWER)
        target_token, target_id = await _register_verify_login(client, mock_send_email, _TARGET)
        await _seed_profile(client, target_token)
        await _set_account_status(db_session, target_id, AccountStatus.SUSPENDED)

        resp = await client.get(
            f"{PROFILES_URL}/{target_id}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_blocked_account_returns_404(self, client, mock_send_email, db_session):
        viewer_token, _ = await _register_verify_login(client, mock_send_email, _VIEWER)
        target_token, target_id = await _register_verify_login(client, mock_send_email, _TARGET)
        await _seed_profile(client, target_token)
        await _set_account_status(db_session, target_id, AccountStatus.BLOCKED)

        resp = await client.get(
            f"{PROFILES_URL}/{target_id}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_deleted_account_returns_404(self, client, mock_send_email, db_session):
        viewer_token, _ = await _register_verify_login(client, mock_send_email, _VIEWER)
        target_token, target_id = await _register_verify_login(client, mock_send_email, _TARGET)
        await _seed_profile(client, target_token)
        await _set_account_status(db_session, target_id, AccountStatus.DELETED)

        resp = await client.get(
            f"{PROFILES_URL}/{target_id}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_404_body_does_not_leak_account_state(self, client, mock_send_email, db_session):
        """Response must not contain 'suspended', 'blocked', or 'deleted'."""
        viewer_token, _ = await _register_verify_login(client, mock_send_email, _VIEWER)
        target_token, target_id = await _register_verify_login(client, mock_send_email, _TARGET)
        await _seed_profile(client, target_token)

        for status in (AccountStatus.SUSPENDED, AccountStatus.BLOCKED, AccountStatus.DELETED):
            await _set_account_status(db_session, target_id, status)
            resp = await client.get(
                f"{PROFILES_URL}/{target_id}",
                headers={"Authorization": f"Bearer {viewer_token}"},
            )
            body = resp.text.lower()
            assert "suspended" not in body
            assert "blocked" not in body
            assert "deleted" not in body

    @pytest.mark.asyncio
    async def test_nonexistent_user_id_returns_404(self, client, mock_send_email):
        viewer_token, _ = await _register_verify_login(client, mock_send_email, _VIEWER)

        resp = await client.get(
            f"{PROFILES_URL}/99999",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 404
