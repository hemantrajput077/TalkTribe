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

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.infrastructure.token_model import RefreshToken


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
        record = await self._get_by_token(token)
        if record is None:
            return False
        record.is_revoked = True
        await self.db.commit()
        return True

    async def revoke_all_user_tokens(self, user_id: int) -> int:
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
        now = datetime.now(UTC)
        result = await self.db.execute(delete(RefreshToken).where(RefreshToken.expires_at < now))
        await self.db.commit()
        return result.rowcount  # type: ignore[attr-defined]

    async def get_valid_token(self, token: str) -> RefreshToken | None:
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.is_revoked == False,  # noqa: E712
                RefreshToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def _get_by_token(self, token: str) -> RefreshToken | None:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token == token))
        return result.scalar_one_or_none()
