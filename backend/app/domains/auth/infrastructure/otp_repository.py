from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.infrastructure.otp_model import Otp


class OtpRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        user_id: int,
        otp_code: str,
        purpose: str,
        expires_at: datetime,
    ) -> Otp:
        otp_record = Otp(
            user_id=user_id,
            otp=otp_code,
            purpose=purpose,
            expires_at=expires_at,
            is_used=False,
        )
        self.db.add(otp_record)
        await self.db.commit()
        await self.db.refresh(otp_record)
        return otp_record

    async def get_valid(self, user_id: int, purpose: str) -> Otp | None:
        result = await self.db.execute(
            select(Otp)
            .where(
                and_(
                    Otp.user_id == user_id,
                    Otp.purpose == purpose,
                    Otp.is_used == False,  # noqa: E712
                    Otp.expires_at > datetime.utcnow(),
                )
            )
            .order_by(Otp.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def expire_all(self, user_id: int, purpose: str) -> None:
        result = await self.db.execute(
            select(Otp).where(
                and_(
                    Otp.user_id == user_id,
                    Otp.purpose == purpose,
                    Otp.is_used == False,  # noqa: E712
                )
            )
        )
        for otp in result.scalars().all():
            otp.is_used = True
        await self.db.commit()
