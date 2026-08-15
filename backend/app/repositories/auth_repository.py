"""
Auth repository — pure DB access for refresh-token lifecycle.

Responsibilities:
  - Persist a new refresh token (after login / token rotation)
  - Retrieve a token record by token string
  - Revoke a specific token (logout)
  - Revoke all tokens for a user (logout-all / password change)
  - Purge expired tokens (called by a scheduler or startup task)
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.refresh_token import RefreshToken


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Write ────────────────────────────────────────────────────────────────

    async def save_refresh_token(
        self,
        user_id: int,
        token: str,
        expires_at: datetime,
    ) -> RefreshToken:
        record = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def revoke_token(self, token: str) -> bool:
        """Mark a single refresh token as revoked. Returns True if found."""
        record = await self._get_by_token(token)
        if record is None:
            return False
        record.is_revoked = True
        await self.db.commit()
        return True

    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke every active refresh token for a user. Returns count revoked."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
        )
        records = result.scalars().all()

        for r in records:
            r.is_revoked = True

        await self.db.commit()
        return len(records)

    async def delete_expired_tokens(self) -> int:
        """Hard-delete expired tokens. Call from a background task."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < now)
        )
        await self.db.commit()
        return result.rowcount  # type: ignore[return-value]

    # ── Read ─────────────────────────────────────────────────────────────────

    async def get_valid_token(self, token: str) -> RefreshToken | None:
        """Return the RefreshToken only if it exists, is not revoked, and not expired."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.is_revoked == False,  # noqa: E712
                RefreshToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    # ── Private ──────────────────────────────────────────────────────────────

    async def _get_by_token(self, token: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()
