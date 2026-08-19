"""
test_schemas.py — Pydantic schema validation unit tests.

These tests exercise the schema validation logic in isolation —
no database, no HTTP, no external services required.
"""

import pytest
from pydantic import ValidationError


class TestCreateUser:
    """Unit tests for the CreateUser registration schema."""

    def test_valid_user(self):
        from app.domains.auth.schemas.auth import CreateUser

        user = CreateUser(
            username="testuser",
            email="test@example.com",
            password="SecurePass1!",
            full_name="Test User",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_email_normalized_to_lowercase(self):
        from app.domains.auth.schemas.auth import CreateUser

        user = CreateUser(
            username="testuser",
            email="TEST@EXAMPLE.COM",
            password="SecurePass1!",
        )
        assert user.email == "test@example.com"

    def test_username_too_short(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(username="ab", email="t@e.com", password="SecurePass1!")

    def test_username_reserved(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(username="admin", email="t@e.com", password="SecurePass1!")

    def test_password_missing_uppercase(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(username="testuser", email="t@e.com", password="nouppercase1!")

    def test_password_missing_digit(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(username="testuser", email="t@e.com", password="NoDigitPass!")

    def test_password_missing_special(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(username="testuser", email="t@e.com", password="NoSpecial123")

    def test_extra_fields_forbidden(self):
        from app.domains.auth.schemas.auth import CreateUser

        with pytest.raises(ValidationError):
            CreateUser(
                username="testuser",
                email="t@e.com",
                password="SecurePass1!",
                unknown_field="value",
            )


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
