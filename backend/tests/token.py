from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    get_token_jti,
    _decode
)
from app.core.config import settings

token = create_access_token(user_id=1, email="test@gmail.com")
print(token)

refresh_token, expire = create_refresh_token(user_id=1, email="test@gmail.com")
print(refresh_token)
print(expire)

payload = verify_refresh_token(refresh_token)
print(payload)

jti = get_token_jti(token, "access")
print(jti)

decode = _decode(token, settings.SECRET_KEY)
print(decode)

payload = verify_access_token(token)
print(payload)


# The circular import is caused by running python token.py from the tests/ directory — Python adds tests/ to sys.path, so import app.core.jwt triggers the full app package init chain. The app/models/__init__.py eagerly imports User and RefreshToken → which imports app.db.base → which may re-import something that imports app.core.jwt before it finishes loading
# The real fix is two things:
# Fix 1: Remove decode from the import (it doesn't exist — it's _decode, a private helper)
# Fix 2: Run the test from the backend/ directory (not tests/), which is already the correct working directory for the app package resolution