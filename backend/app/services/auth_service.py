"""
Auth service — orchestrates user authentication and token lifecycle.

What this layer does:
  - Validates credentials (username + bcrypt password)
  - Issues access + refresh tokens on login
  - Rotates refresh tokens (old token revoked, new one issued)
  - Logs the user out (revokes all tokens)
  - Provides get_current_user FastAPI dependency
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.security.jwt import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from app.infrastructure.security.password import hash_password, verify_password
from app.infrastructure.database.dependencies import get_db
from app.models.auth import User
from app.repositories.auth_repository import AuthRepository
from app.schemas.token import Token

bearer_scheme = HTTPBearer()


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuthRepository(db)

    # ── User lookup helpers ──────────────────────────────────────────────────

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def check_username_exist(self, username: str) -> bool:
        return await self.get_user_by_username(username) is not None

    async def check_email_exist(self, email: str) -> bool:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none() is not None

    # ── Registration ─────────────────────────────────────────────────────────

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> User:
        user = User(
            username=username,
            email=email,
            password=hash_password(password),
            full_name=full_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    # ── Login ────────────────────────────────────────────────────────────────

    async def authenticate_user(self, username: str, password: str) -> User:
        """Return User on success; raise HTTP 401/403 on failure."""
        user = await self.get_user_by_username(username)

        # Constant-time check even when user doesn't exist — prevents
        # user-enumeration via response timing.
        dummy_hash = "$2b$12$notarealhashjustpadding....................."  # intentional dummy for constant-time compare
        stored_hash = user.password if user else dummy_hash

        if not verify_password(password, stored_hash) or user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please verify your email using the OTP sent to your inbox.",
            )

        return user

    async def login(self, username: str, password: str) -> Token:
        """Authenticate and return a fresh access + refresh token pair."""
        user = await self.authenticate_user(username, password)
        return await self._issue_tokens(user)

    # ── Token rotation ───────────────────────────────────────────────────────

    async def refresh_tokens(self, refresh_token: str) -> Token:
        """Validate incoming refresh token, revoke it, issue a new pair."""
        payload = verify_refresh_token(refresh_token)

        record = await self.repo.get_valid_token(refresh_token)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or has been revoked.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await self.get_user_by_id(int(payload["sub"]))
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive.",
            )

        await self.repo.revoke_token(refresh_token)
        return await self._issue_tokens(user)

    # ── Logout ───────────────────────────────────────────────────────────────

    async def logout(self, refresh_token: str) -> None:
        await self.repo.revoke_token(refresh_token)

    async def logout_all(self, user_id: int) -> None:
        await self.repo.revoke_all_user_tokens(user_id)

    # ── Internal ─────────────────────────────────────────────────────────────

    async def _issue_tokens(self, user: User) -> Token:
        access_token = create_access_token(user.id, user.email)
        refresh_token, expires_at = create_refresh_token(user.id, user.email)
        await self.repo.save_refresh_token(user.id, refresh_token, expires_at)
        return Token(access_token=access_token, refresh_token=refresh_token)


# ── FastAPI dependency helpers ───────────────────────────────────────────────


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the Bearer access token,
    then returns the authenticated User. Use with Depends() in any route.
    """
    token = credentials.credentials
    payload = verify_access_token(token)

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

    return user
