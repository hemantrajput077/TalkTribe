"""
AuthService — orchestrates user authentication and token lifecycle.

Responsibilities:
  - User lookup / existence checks
  - Password hashing on registration
  - Credential validation on login
  - JWT access + refresh token issuance
  - Refresh token rotation (revoke old → issue new pair)
  - Single-device and all-device logout
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.dependencies import get_db
from app.infrastructure.cache.redis import blocklist_token
from app.infrastructure.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token_unverified_exp,
    verify_refresh_token,
)
from app.infrastructure.security.password import hash_password, verify_password
from app.domains.auth.infrastructure.user_model import User
from app.domains.auth.infrastructure.repository import AuthRepository
from app.domains.auth.schemas.token import Token


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuthRepository(db)

    # ── User lookups ─────────────────────────────────────────────────────────

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
        user = await self.get_user_by_username(username)

        # Constant-time path even when user doesn't exist (prevents timing attacks).
        dummy_hash = "$2b$12$notarealhashjustpadding....................."
        stored_hash = user.password if user else dummy_hash

        if not verify_password(password, stored_hash) or user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please verify your email using the OTP sent to your inbox.",
            )
        return user

    async def login(self, username: str, password: str) -> Token:
        user = await self.authenticate_user(username, password)
        return await self._issue_tokens(user)

    # ── Token rotation ───────────────────────────────────────────────────────

    async def refresh_tokens(self, refresh_token: str, access_token: str) -> Token:
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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")

        # Blocklist the old access token so it can't be used after this rotation.
        at_payload = decode_access_token_unverified_exp(access_token)
        exp = datetime.fromtimestamp(at_payload["exp"], tz=UTC)
        await blocklist_token(at_payload["jti"], exp)

        await self.repo.revoke_token(refresh_token)
        return await self._issue_tokens(user)

    # ── Logout ───────────────────────────────────────────────────────────────

    async def logout(self, refresh_token: str, access_token: str) -> None:
        at_payload = decode_access_token_unverified_exp(access_token)
        exp = datetime.fromtimestamp(at_payload["exp"], tz=UTC)
        await blocklist_token(at_payload["jti"], exp)
        await self.repo.revoke_token(refresh_token)

    async def logout_all(self, user_id: int) -> None:
        await self.repo.revoke_all_user_tokens(user_id)

    # ── Internal ─────────────────────────────────────────────────────────────

    async def _issue_tokens(self, user: User) -> Token:
        access_token = create_access_token(user.id, user.email)
        refresh_token, expires_at = create_refresh_token(user.id, user.email)
        await self.repo.save_refresh_token(user.id, refresh_token, expires_at)
        return Token(access_token=access_token, refresh_token=refresh_token)


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)
