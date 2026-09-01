"""
API-level FastAPI dependencies.

get_current_user lives here — at the transport boundary — so every future domain
can use it via Depends(get_current_user) without importing the auth service module.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.domain.enums import AccountStatus
from app.domains.auth.infrastructure.user_model import User
from app.domains.auth.schemas.identity import AuthenticatedIdentity
from app.infrastructure.cache.redis import is_blocklisted
from app.infrastructure.database.dependencies import get_db
from app.infrastructure.security.jwt import verify_access_token

bearer_scheme = HTTPBearer()

_REJECTED_STATUSES = {
    AccountStatus.PENDING_VERIFICATION: "EMAIL_NOT_VERIFIED",
    AccountStatus.SUSPENDED: "ACCOUNT_SUSPENDED",
    AccountStatus.BLOCKED: "ACCOUNT_BLOCKED",
    AccountStatus.DELETED: "ACCOUNT_DELETED",
}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedIdentity:
    """
    Validate the Bearer token, read role + account_status from DB, and return
    AuthenticatedIdentity. Any domain can Depends(get_current_user) without
    importing auth infrastructure.
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )

    if user.account_status in _REJECTED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_REJECTED_STATUSES[user.account_status],
        )

    return AuthenticatedIdentity(
        user_id=user.id,
        role=user.role,
        account_status=user.account_status,
        is_verified=user.account_status != AccountStatus.PENDING_VERIFICATION,
    )
