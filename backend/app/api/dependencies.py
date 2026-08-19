"""
API-level FastAPI dependencies.

get_current_user lives here — at the transport boundary — so every future domain
can use it via Depends(get_current_user) without importing the auth service module.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis import is_blocklisted
from app.infrastructure.database.dependencies import get_db
from app.infrastructure.security.jwt import verify_access_token
from app.domains.auth.infrastructure.user_model import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the Bearer access token; return the authenticated User.
    Use with Depends(get_current_user) in any protected route.
    """
    token = credentials.credentials
    payload = verify_access_token(token)

    if await is_blocklisted(payload["jti"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

    return user
