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

from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import hash_password, verify_password
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from app.db.dependencies import get_db
from app.models.auth import User
from app.models.refresh_token import RefreshToken
from app.repositories.auth_repository import AuthRepository
from app.schemas.token import Token

bearer_scheme = HTTPBearer()


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuthRepository(db)

    # ── User lookup helpers ──────────────────────────────────────────────────

    def get_user_by_username(self, username: str) -> User | None:
        return self.db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def check_username_exist(self, username: str) -> bool:
        return self.get_user_by_username(username) is not None

    def check_email_exist(self, email: str) -> bool:
        result = self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        return result is not None

    # ── Registration ─────────────────────────────────────────────────────────

    def create_user(self, username: str, email: str, password: str, full_name: str | None = None) -> User:
        user = User(
            username=username,
            email=email,
            password=hash_password(password),   # bcrypt hash, never plain-text
            full_name=full_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # ── Login ────────────────────────────────────────────────────────────────

    def authenticate_user(self, username: str, password: str) -> User:
        """Return User on success; raise HTTP 401 on failure."""
        user = self.get_user_by_username(username)

        # Use a constant-time comparison even when the user is not found
        # to prevent user-enumeration via timing differences.
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
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )

        return user

    def login(self, username: str, password: str) -> Token:
        """Authenticate and return a fresh access + refresh token pair."""
        user = self.authenticate_user(username, password)
        return self._issue_tokens(user)

    # ── Token rotation ───────────────────────────────────────────────────────

    def refresh_tokens(self, refresh_token: str) -> Token:
        """
        Validate the incoming refresh token, revoke it (rotation),
        and issue a brand-new token pair.
        """
        # 1. Cryptographically verify the JWT
        payload = verify_refresh_token(refresh_token)

        # 2. Check the DB — must exist, not revoked, not expired
        record = self.repo.get_valid_token(refresh_token)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or has been revoked.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = self.get_user_by_id(int(payload["sub"]))
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive.",
            )

        # 3. Revoke the used token (rotation — prevents reuse)
        self.repo.revoke_token(refresh_token)

        # 4. Issue a new pair
        return self._issue_tokens(user)

    # ── Logout ───────────────────────────────────────────────────────────────

    def logout(self, refresh_token: str) -> None:
        """Revoke the supplied refresh token."""
        self.repo.revoke_token(refresh_token)

    def logout_all(self, user_id: int) -> None:
        """Revoke every refresh token for the user (e.g., password change)."""
        self.repo.revoke_all_user_tokens(user_id)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _issue_tokens(self, user: User) -> Token:
        access_token = create_access_token(user.id, user.email)
        refresh_token, expires_at = create_refresh_token(user.id, user.email)
        self.repo.save_refresh_token(user.id, refresh_token, expires_at)
        return Token(access_token=access_token, refresh_token=refresh_token)


# ── FastAPI dependency helpers ───────────────────────────────────────────────

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the Bearer access token,
    then returns the authenticated User.  Use with Depends() in any route.

    Usage:
        @router.get("/me")
        def me(user: User = Depends(get_current_user)):
            ...
    """
    token = credentials.credentials
    payload = verify_access_token(token)

    user_id: int = int(payload["sub"])
    user = db.get(User, user_id)

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


# legacy alias kept for backward compatibility
def auth_service_dependency(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)