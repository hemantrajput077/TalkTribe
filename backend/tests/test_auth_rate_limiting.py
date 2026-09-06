"""
Endpoint-level rate-limiting tests for auth routes.

The `client` fixture (from conftest) mocks all rate-limit functions as
no-ops by default. Each test class uses nested patches to override
individual functions and assert the correct HTTP behaviour.
"""

from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, status

_RATE_LIMIT_EXC = HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail="AUTH_RATE_LIMIT_EXCEEDED",
    headers={"Retry-After": "42"},
)
_COOLDOWN_EXC = HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail="AUTH_OTP_RESEND_COOLDOWN",
    headers={"Retry-After": "30"},
)

_REGISTER_PAYLOAD = {
    "username": "ratelimituser",
    "email": "ratelimit@example.com",
    "phone_number": "+919876543211",
    "password": "SecurePass1!",
    "full_name": "Rate Limit User",
}
_LOGIN_PAYLOAD = {"username": "ratelimituser", "password": "SecurePass1!"}
_RESEND_EMAIL = {"email": "ratelimit@example.com"}
_VERIFY_PAYLOAD = {"email": "ratelimit@example.com", "otp": "123456"}


# ── /register ─────────────────────────────────────────────────────────────────


class TestRegisterRateLimit:
    async def test_under_limit_request_succeeds(self, client):
        resp = await client.post("/api/v1/auth/register", json=_REGISTER_PAYLOAD)
        # conftest mocks rate-limit as no-op; registration itself may fail for
        # other reasons (duplicate) but must not be blocked by rate limiting.
        assert resp.status_code != 429

    async def test_over_ip_limit_returns_429(self, client):
        with patch(
            "app.domains.auth.api.routes.check_register_rate_limit",
            new_callable=AsyncMock,
            side_effect=_RATE_LIMIT_EXC,
        ):
            resp = await client.post("/api/v1/auth/register", json=_REGISTER_PAYLOAD)
        assert resp.status_code == 429
        assert resp.json()["detail"] == "AUTH_RATE_LIMIT_EXCEEDED"
        assert resp.headers["Retry-After"] == "42"

    async def test_over_limit_response_includes_retry_after(self, client):
        with patch(
            "app.domains.auth.api.routes.check_register_rate_limit",
            new_callable=AsyncMock,
            side_effect=_RATE_LIMIT_EXC,
        ):
            resp = await client.post("/api/v1/auth/register", json=_REGISTER_PAYLOAD)
        assert "Retry-After" in resp.headers


# ── /login ────────────────────────────────────────────────────────────────────


class TestLoginRateLimit:
    async def test_ip_limit_returns_429(self, client):
        with patch(
            "app.domains.auth.api.routes.check_login_rate_limit",
            new_callable=AsyncMock,
            side_effect=_RATE_LIMIT_EXC,
        ):
            resp = await client.post("/api/v1/auth/login", json=_LOGIN_PAYLOAD)
        assert resp.status_code == 429
        assert resp.json()["detail"] == "AUTH_RATE_LIMIT_EXCEEDED"

    async def test_rate_limit_fires_before_password_verification(self, client):
        """Rate limit must raise before the auth service is ever called."""
        with (
            patch(
                "app.domains.auth.api.routes.check_login_rate_limit",
                new_callable=AsyncMock,
                side_effect=_RATE_LIMIT_EXC,
            ),
            patch(
                "app.domains.auth.api.routes.get_auth_service",
            ) as mock_factory,
        ):
            resp = await client.post("/api/v1/auth/login", json=_LOGIN_PAYLOAD)

        assert resp.status_code == 429
        # Dependency factory was never invoked — auth service never ran
        mock_factory.assert_not_called()

    async def test_login_retry_after_header_present(self, client):
        with patch(
            "app.domains.auth.api.routes.check_login_rate_limit",
            new_callable=AsyncMock,
            side_effect=_RATE_LIMIT_EXC,
        ):
            resp = await client.post("/api/v1/auth/login", json=_LOGIN_PAYLOAD)
        assert "Retry-After" in resp.headers


# ── /verify-email ─────────────────────────────────────────────────────────────


class TestVerifyEmailRateLimit:
    async def test_over_limit_returns_429(self, client):
        with patch(
            "app.domains.auth.api.routes.check_verify_email_rate_limit",
            new_callable=AsyncMock,
            side_effect=_RATE_LIMIT_EXC,
        ):
            resp = await client.post("/api/v1/auth/verify-email", json=_VERIFY_PAYLOAD)
        assert resp.status_code == 429
        assert resp.json()["detail"] == "AUTH_RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in resp.headers

    async def test_verify_rate_limit_fires_before_otp_check(self, client):
        """OTP lookup must not happen when the rate limit is exceeded."""
        with (
            patch(
                "app.domains.auth.api.routes.check_verify_email_rate_limit",
                new_callable=AsyncMock,
                side_effect=_RATE_LIMIT_EXC,
            ),
            patch(
                "app.domains.auth.api.routes.verify_otp",
                new_callable=AsyncMock,
            ) as mock_verify,
        ):
            resp = await client.post("/api/v1/auth/verify-email", json=_VERIFY_PAYLOAD)
        assert resp.status_code == 429
        mock_verify.assert_not_called()


# ── /resend-otp ───────────────────────────────────────────────────────────────


class TestResendOTPRateLimit:
    async def test_window_limit_returns_429(self, client):
        with patch(
            "app.domains.auth.api.routes.check_resend_otp_rate_limit",
            new_callable=AsyncMock,
            side_effect=_RATE_LIMIT_EXC,
        ):
            resp = await client.post("/api/v1/auth/resend-otp", json=_RESEND_EMAIL)
        assert resp.status_code == 429
        assert resp.json()["detail"] == "AUTH_RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in resp.headers

    async def test_cooldown_returns_429_with_specific_detail(self, client):
        with (
            patch(
                "app.domains.auth.api.routes.check_resend_otp_rate_limit",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.auth.api.routes.acquire_resend_otp_cooldown",
                new_callable=AsyncMock,
                side_effect=_COOLDOWN_EXC,
            ),
        ):
            resp = await client.post("/api/v1/auth/resend-otp", json=_RESEND_EMAIL)
        assert resp.status_code == 429
        assert resp.json()["detail"] == "AUTH_OTP_RESEND_COOLDOWN"
        assert resp.headers["Retry-After"] == "30"

    async def test_otp_not_sent_when_window_limit_exceeded(self, client, mock_send_email):
        with patch(
            "app.domains.auth.api.routes.check_resend_otp_rate_limit",
            new_callable=AsyncMock,
            side_effect=_RATE_LIMIT_EXC,
        ):
            await client.post("/api/v1/auth/resend-otp", json=_RESEND_EMAIL)
        mock_send_email.assert_not_called()

    async def test_otp_not_sent_when_cooldown_active(self, client, mock_send_email):
        with (
            patch(
                "app.domains.auth.api.routes.check_resend_otp_rate_limit",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.auth.api.routes.acquire_resend_otp_cooldown",
                new_callable=AsyncMock,
                side_effect=_COOLDOWN_EXC,
            ),
        ):
            await client.post("/api/v1/auth/resend-otp", json=_RESEND_EMAIL)
        mock_send_email.assert_not_called()

    async def test_cooldown_released_when_otp_service_raises(self, client):
        """If resend_otp raises (e.g. user not found), the cooldown must be released."""
        with (
            patch(
                "app.domains.auth.api.routes.check_resend_otp_rate_limit",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.auth.api.routes.acquire_resend_otp_cooldown",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.auth.api.routes.release_resend_otp_cooldown",
                new_callable=AsyncMock,
            ) as mock_release,
            patch(
                "app.domains.auth.api.routes.resend_otp",
                new_callable=AsyncMock,
                side_effect=HTTPException(status_code=404, detail="User not found"),
            ),
        ):
            resp = await client.post("/api/v1/auth/resend-otp", json=_RESEND_EMAIL)
        assert resp.status_code == 404
        mock_release.assert_called_once()

    async def test_cooldown_released_when_email_send_fails(self, client, mock_send_email):
        """If email sending fails after cooldown is acquired, cooldown must be released."""
        mock_send_email.return_value = False

        with (
            patch(
                "app.domains.auth.api.routes.check_resend_otp_rate_limit",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.auth.api.routes.acquire_resend_otp_cooldown",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.auth.api.routes.release_resend_otp_cooldown",
                new_callable=AsyncMock,
            ) as mock_release,
            patch(
                "app.domains.auth.api.routes.resend_otp",
                new_callable=AsyncMock,
                return_value=("123456", "testuser"),
            ),
        ):
            resp = await client.post("/api/v1/auth/resend-otp", json=_RESEND_EMAIL)
        assert resp.status_code == 500
        mock_release.assert_called_once()

    async def test_successful_resend_does_not_release_cooldown(self, client, mock_send_email):
        """On success the cooldown key stays — release must NOT be called."""
        with (
            patch(
                "app.domains.auth.api.routes.check_resend_otp_rate_limit",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.auth.api.routes.acquire_resend_otp_cooldown",
                new_callable=AsyncMock,
            ),
            patch(
                "app.domains.auth.api.routes.release_resend_otp_cooldown",
                new_callable=AsyncMock,
            ) as mock_release,
            patch(
                "app.domains.auth.api.routes.resend_otp",
                new_callable=AsyncMock,
                return_value=("123456", "testuser"),
            ),
        ):
            resp = await client.post("/api/v1/auth/resend-otp", json=_RESEND_EMAIL)
        assert resp.status_code == 200
        mock_release.assert_not_called()
