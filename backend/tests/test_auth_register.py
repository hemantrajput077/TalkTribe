"""
test_auth_register.py — Registration endpoint tests.

Covers:
  - Successful registration (201 + email sent)
  - Input validation failures (422)
  - Duplicate field conflicts (409)
  - Email delivery failure (500)
"""

from unittest.mock import AsyncMock, patch

import pytest

REGISTER_URL = "/api/v1/auth/register"

BASE_PAYLOAD = {
    "username": "newuser",
    "email": "new@example.com",
    "phone_number": "+919876543210",
    "password": "SecurePass1!",
}


class TestRegisterSuccess:
    @pytest.mark.asyncio
    async def test_returns_201(self, client):
        response = await client.post(REGISTER_URL, json=BASE_PAYLOAD)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_response_contains_message(self, client):
        response = await client.post(REGISTER_URL, json=BASE_PAYLOAD)
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_email_sent_to_correct_address(self, client, mock_send_email):
        await client.post(REGISTER_URL, json=BASE_PAYLOAD)
        mock_send_email.assert_called_once()
        email_arg = mock_send_email.call_args[0][0]
        assert email_arg == BASE_PAYLOAD["email"]

    @pytest.mark.asyncio
    async def test_otp_is_6_digits(self, client, mock_send_email):
        await client.post(REGISTER_URL, json=BASE_PAYLOAD)
        otp_arg = mock_send_email.call_args[0][1]
        assert len(otp_arg) == 6
        assert otp_arg.isdigit()

    @pytest.mark.asyncio
    async def test_optional_full_name_accepted(self, client):
        payload = {**BASE_PAYLOAD, "full_name": "New User"}
        response = await client.post(REGISTER_URL, json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_without_full_name_accepted(self, client):
        response = await client.post(REGISTER_URL, json=BASE_PAYLOAD)
        assert response.status_code == 201


class TestRegisterValidation:
    @pytest.mark.asyncio
    async def test_missing_phone_number_returns_422(self, client):
        payload = {k: v for k, v in BASE_PAYLOAD.items() if k != "phone_number"}
        response = await client.post(REGISTER_URL, json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_phone_without_plus_returns_422(self, client):
        response = await client.post(REGISTER_URL, json={**BASE_PAYLOAD, "phone_number": "919876543210"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_phone_too_short_returns_422(self, client):
        response = await client.post(REGISTER_URL, json={**BASE_PAYLOAD, "phone_number": "+12345"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_username_returns_422(self, client):
        payload = {k: v for k, v in BASE_PAYLOAD.items() if k != "username"}
        response = await client.post(REGISTER_URL, json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_email_returns_422(self, client):
        payload = {k: v for k, v in BASE_PAYLOAD.items() if k != "email"}
        response = await client.post(REGISTER_URL, json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_password_returns_422(self, client):
        payload = {k: v for k, v in BASE_PAYLOAD.items() if k != "password"}
        response = await client.post(REGISTER_URL, json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_email_returns_422(self, client):
        response = await client.post(REGISTER_URL, json={**BASE_PAYLOAD, "email": "notanemail"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_reserved_username_returns_422(self, client):
        response = await client.post(REGISTER_URL, json={**BASE_PAYLOAD, "username": "admin"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_username_too_short_returns_422(self, client):
        response = await client.post(REGISTER_URL, json={**BASE_PAYLOAD, "username": "ab"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_weak_password_no_uppercase_returns_422(self, client):
        response = await client.post(REGISTER_URL, json={**BASE_PAYLOAD, "password": "weakpass1!"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_weak_password_no_digit_returns_422(self, client):
        response = await client.post(REGISTER_URL, json={**BASE_PAYLOAD, "password": "WeakPass!!"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_weak_password_no_special_returns_422(self, client):
        response = await client.post(REGISTER_URL, json={**BASE_PAYLOAD, "password": "WeakPass123"})
        assert response.status_code == 422


class TestRegisterConflicts:
    @pytest.mark.asyncio
    async def test_duplicate_username_returns_409(self, client):
        await client.post(REGISTER_URL, json=BASE_PAYLOAD)
        response = await client.post(REGISTER_URL, json={
            **BASE_PAYLOAD,
            "email": "other@example.com",
            "phone_number": "+911234567890",
        })
        assert response.status_code == 409
        assert response.json()["detail"] == "USERNAME_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_409(self, client):
        await client.post(REGISTER_URL, json=BASE_PAYLOAD)
        response = await client.post(REGISTER_URL, json={
            **BASE_PAYLOAD,
            "username": "otheruser",
            "phone_number": "+911234567890",
        })
        assert response.status_code == 409
        assert response.json()["detail"] == "EMAIL_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_duplicate_phone_returns_409(self, client):
        await client.post(REGISTER_URL, json=BASE_PAYLOAD)
        response = await client.post(REGISTER_URL, json={
            **BASE_PAYLOAD,
            "username": "otheruser",
            "email": "other@example.com",
        })
        assert response.status_code == 409
        assert response.json()["detail"] == "PHONE_ALREADY_EXISTS"


class TestRegisterEmailFailure:
    @pytest.mark.asyncio
    async def test_email_failure_returns_500(self, client):
        with patch(
            "app.domains.auth.api.routes.send_otp_email",
            new_callable=AsyncMock,
            return_value=False,
        ):
            response = await client.post(REGISTER_URL, json=BASE_PAYLOAD)
        assert response.status_code == 500
