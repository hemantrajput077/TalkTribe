"""
Password hashing using pwdlib (bcrypt) — modern replacement for passlib.
pwdlib is fully compatible with latest bcrypt versions.
"""

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

_pwd_context = PasswordHash([BcryptHasher()])


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    return _pwd_context.verify(plain, hashed)
