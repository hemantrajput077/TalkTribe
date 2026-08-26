"""
test_schemas.py — Pydantic schema validation unit tests.

No database, no HTTP, no external services required.
"""

import pytest
from pydantic import ValidationError


def valid_user(**overrides):
    base = {
        "username": "testuser",
        "email": "test@example.com",
        "phone_number": "+919876543210",
        "password": "SecurePass1!",
    }
    return {**base, **overrides}


class TestCreateUser:
    """Unit tests for the CreateUser registration schema."""

    def test_valid_user(self):
        from app.domains.auth.schemas.auth import CreateUser

        user = CreateUser(**valid_user(full_name="Test User"))
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.phone_number == "+919876543210"

    def test_email_normalized_to_lowercase(self):
        from app.domains.auth.schemas.auth import CreateUser

        user = CreateUser(**valid_user(email="TEST@EXAMPLE.COM"))
        assert user.email == "test@example.com"

    def test_username_too_short(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(**valid_user(username="ab"))

    def test_username_reserved(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(**valid_user(username="admin"))

    def test_password_missing_uppercase(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(**valid_user(password="nouppercase1!"))

    def test_password_missing_digit(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(**valid_user(password="NoDigitPass!"))

    def test_password_missing_special(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(**valid_user(password="NoSpecial123"))

    def test_extra_fields_forbidden(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(**valid_user(unknown_field="value"))

    # ── Phone number validation ───────────────────────────────────────────────

    def test_phone_number_required(self):
        from app.domains.auth.schemas.auth import CreateUser

        data = valid_user()
        del data["phone_number"]
        with pytest.raises(ValidationError):
            CreateUser(**data)

    def test_phone_number_valid_india(self):
        from app.domains.auth.schemas.auth import CreateUser

        user = CreateUser(**valid_user(phone_number="+919876543210"))
        assert user.phone_number == "+919876543210"

    def test_phone_number_valid_us(self):
        from app.domains.auth.schemas.auth import CreateUser

        user = CreateUser(**valid_user(phone_number="+12025550123"))
        assert user.phone_number == "+12025550123"

    def test_phone_number_no_plus_rejected(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(**valid_user(phone_number="919876543210"))

    def test_phone_number_too_short_rejected(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(**valid_user(phone_number="+1234567"))

    def test_phone_number_leading_zero_after_plus_rejected(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(**valid_user(phone_number="+0919876543210"))

    def test_phone_number_whitespace_stripped(self):
        from app.domains.auth.schemas.auth import CreateUser

        user = CreateUser(**valid_user(phone_number="  +919876543210  "))
        assert user.phone_number == "+919876543210"

    def test_phone_number_letters_rejected(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(**valid_user(phone_number="+91987654abcd"))


class TestUserLogin:
    """Unit tests for the UserLogin schema."""

    def test_valid_login(self):
        from app.domains.auth.schemas.auth import UserLogin

        login = UserLogin(username="testuser", password="SecurePass1!")
        assert login.username == "testuser"

    def test_reserved_username_rejected(self):
        from app.domains.auth.schemas.auth import UserLogin

        with pytest.raises(ValidationError):
            UserLogin(username="root", password="SecurePass1!")
