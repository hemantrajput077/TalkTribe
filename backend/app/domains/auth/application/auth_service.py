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
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.infrastructure.repository import AuthRepository
from app.domains.auth.infrastructure.user_model import User
from app.domains.auth.infrastructure.user_repository import UserRepository
from app.domains.auth.schemas.token import Token
from app.infrastructure.cache.redis import blocklist_token
from app.infrastructure.database.dependencies import get_db
from app.infrastructure.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token_unverified_exp,
    verify_refresh_token,
)
from app.infrastructure.security.password import hash_password, verify_password


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuthRepository(db)
        self.user_repo = UserRepository(db)

    # ── User lookups ─────────────────────────────────────────────────────────

    async def get_user_by_username(self, username: str) -> User | None:
        return await self.user_repo.get_by_username(username)

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.user_repo.get_by_id(user_id)

    async def check_username_exist(self, username: str) -> bool:
        return await self.user_repo.get_by_username(username) is not None

    async def check_email_exist(self, email: str) -> bool:
        return await self.user_repo.get_by_email(email) is not None

    async def check_phone_number_exist(self, phone_number: str) -> bool:
        return await self.user_repo.get_by_phone_number(phone_number) is not None

    # ── Registration ─────────────────────────────────────────────────────────

    async def create_user(
        self,
        username: str,
        email: str,
        phone_number: str,
        password: str,
        full_name: str | None = None,
    ) -> User:
        return await self.user_repo.create(
            username=username,
            email=email,
            phone_number=phone_number,
            password_hash=hash_password(password),
            full_name=full_name,
        )

    # ── Admin / dev helpers ──────────────────────────────────────────────────

    async def get_all_users(self) -> list[User]:
        return await self.user_repo.get_all()

    async def delete_user_by_id(self, user_id: int) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return False
        await self.user_repo.delete(user)
        return True

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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled."
            )
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive."
            )

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
