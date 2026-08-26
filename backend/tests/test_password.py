"""
test_password.py — Password hashing unit tests.

No database or HTTP client needed — exercises hash_password and verify_password
in isolation.
"""


class TestHashPassword:
    def test_produces_bcrypt_hash(self):
        from app.infrastructure.security.password import hash_password

        hashed = hash_password("SecurePass1!")
        assert hashed.startswith("$2b$")

    def test_hash_is_a_string(self):
        from app.infrastructure.security.password import hash_password

        assert isinstance(hash_password("SecurePass1!"), str)

    def test_same_password_produces_different_hashes(self):
        from app.infrastructure.security.password import hash_password

        h1 = hash_password("SecurePass1!")
        h2 = hash_password("SecurePass1!")
        assert h1 != h2  # bcrypt uses a random salt per call


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        from app.infrastructure.security.password import hash_password, verify_password

        hashed = hash_password("SecurePass1!")
        assert verify_password("SecurePass1!", hashed) is True

    def test_wrong_password_returns_false(self):
        from app.infrastructure.security.password import hash_password, verify_password

        hashed = hash_password("SecurePass1!")
        assert verify_password("WrongPass1!", hashed) is False

    def test_empty_password_returns_false(self):
        from app.infrastructure.security.password import hash_password, verify_password

        hashed = hash_password("SecurePass1!")
        assert verify_password("", hashed) is False

    def test_case_sensitive(self):
        from app.infrastructure.security.password import hash_password, verify_password

        hashed = hash_password("SecurePass1!")
        assert verify_password("securepass1!", hashed) is False
