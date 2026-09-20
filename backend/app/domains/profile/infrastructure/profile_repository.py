from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profile.infrastructure.profile_model import Profile
from app.domains.profile.schemas.profile import ProfileUpdate


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

    async def get_profile_by_id(self, profile_id: int) -> Profile | None:
        result = await self.db.execute(select(Profile).where(Profile.id == profile_id))
        return result.scalar_one_or_none()

    async def update_profile(self, user_id: int, profile_data: ProfileUpdate) -> Profile:
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            raise RuntimeError(f"update_profile called for non-existent user_id={user_id}")
        for field, value in profile_data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def get_safe_profile(self, user_id: int) -> Profile | None:
        result = await self.db.execute(select(Profile).where(Profile.user_id == user_id))
        return result.scalar_one_or_none()
