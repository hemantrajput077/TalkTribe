from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profile.infrastructure.profile_model import Profile


class ProfileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Profile | None:
        result = await self.db.execute(select(Profile).where(Profile.user_id == user_id))
        return result.scalar_one_or_none()

    async def create(self, user_id: int) -> Profile:
        profile = Profile(user_id=user_id)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
