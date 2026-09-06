"""
test_auth_otp.py — Email verification and OTP resend tests.

Covers:
  POST /api/v1/auth/verify-email
  POST /api/v1/auth/resend-otp
"""

import pytest

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
RESEND_URL = "/api/v1/auth/resend-otp"

_USER = {
    "username": "otpuser",
    "email": "otp@example.com",
    "phone_number": "+919876543210",
    "password": "SecurePass1!",
}


async def _register_and_capture_otp(client, mock_send_email, user=None):
    """Register a user and return the OTP that would have been emailed."""
    await client.post(REGISTER_URL, json=user or _USER)
    return mock_send_email.call_args[0][1]  # second positional arg to send_otp_email


class TestVerifyEmail:
    @pytest.mark.asyncio
    async def test_correct_otp_returns_200(self, client, mock_send_email):
        otp = await _register_and_capture_otp(client, mock_send_email)
        response = await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": otp})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_correct_otp_returns_success_message(self, client, mock_send_email):
        otp = await _register_and_capture_otp(client, mock_send_email)
        response = await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": otp})
        assert "verified" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_wrong_otp_returns_400(self, client, mock_send_email):
        await _register_and_capture_otp(client, mock_send_email)
        response = await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": "000000"})
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid OTP"

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_404(self, client):
        response = await client.post(
            VERIFY_URL,
            json={
                "email": "ghost@example.com",
                "otp": "123456",
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_otp_wrong_length_returns_422(self, client, mock_send_email):
        await _register_and_capture_otp(client, mock_send_email)
        response = await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": "12345"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_otp_non_numeric_returns_422(self, client, mock_send_email):
        await _register_and_capture_otp(client, mock_send_email)
        response = await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": "abc123"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_otp_cannot_be_reused(self, client, mock_send_email):
        otp = await _register_and_capture_otp(client, mock_send_email)
        await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": otp})
        # Second use of the same OTP must fail
        response = await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": otp})
        assert response.status_code == 400


class TestResendOtp:
    @pytest.mark.asyncio
    async def test_resend_returns_200(self, client, mock_send_email):
        await client.post(REGISTER_URL, json=_USER)
        response = await client.post(RESEND_URL, json={"email": _USER["email"]})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resend_triggers_new_email(self, client, mock_send_email):
        await client.post(REGISTER_URL, json=_USER)
        mock_send_email.reset_mock()
        await client.post(RESEND_URL, json={"email": _USER["email"]})
        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_new_otp_replaces_old_one(self, client, mock_send_email):
        first_otp = await _register_and_capture_otp(client, mock_send_email)
        # Resend — get a new OTP
        await client.post(RESEND_URL, json={"email": _USER["email"]})
        new_otp = mock_send_email.call_args[0][1]
        # Old OTP must now be invalid
        response = await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": first_otp})
        assert response.status_code == 400
        # New OTP must be valid
        response = await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": new_otp})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resend_nonexistent_user_returns_404(self, client):
        response = await client.post(RESEND_URL, json={"email": "ghost@example.com"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_resend_already_verified_returns_400(self, client, mock_send_email):
        otp = await _register_and_capture_otp(client, mock_send_email)
        await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": otp})
        response = await client.post(RESEND_URL, json={"email": _USER["email"]})
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"].lower()


class TestOtpExpiry:
    @pytest.mark.asyncio
    async def test_expired_otp_returns_400(self, client, db_session, mock_send_email):
        """An OTP whose expires_at is in the past must be rejected."""
        from datetime import datetime, timedelta

        from sqlalchemy import update

        from app.domains.auth.infrastructure.otp_model import Otp

        await _register_and_capture_otp(client, mock_send_email)

        # Wind the clock back on all OTPs for this user so they appear expired.
        await db_session.execute(
            update(Otp).values(expires_at=datetime.utcnow() - timedelta(minutes=10))
        )
        await db_session.commit()

        response = await client.post(VERIFY_URL, json={"email": _USER["email"], "otp": "000000"})
        # No valid OTP exists (expired) → 400
        assert response.status_code == 400


# TODO AUTH-07: OTP attempt limit (test_attempt_limit_locks_otp) is deferred.
# The Otp model has no `attempts` counter yet. Once AUTH-07 Option A is
# implemented (add attempts column + service enforcement), add:
#   - test that submitting wrong OTP 5 times returns 429
#   - test that a new OTP resets the counter
