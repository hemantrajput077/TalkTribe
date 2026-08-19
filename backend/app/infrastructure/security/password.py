from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

_pwd_context = PasswordHash([BcryptHasher()])


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)
