from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profile.infrastructure.profile_model import Profile
from app.domains.profile.infrastructure.profile_repository import ProfileRepository
from app.domains.profile.schemas.profile import ProfileUpdate


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ProfileRepository(db)

    async def get_or_create_profile(self, user_id: int) -> Profile:
        profile = await self.repo.get_by_user_id(user_id)
        if profile is not None:
            return profile

        try:
            return await self.repo.create(user_id)
        except IntegrityError:
            # Two causes possible:
            # 1. UNIQUE violation — a concurrent request already created the profile.
            #    Roll back and re-fetch the row it committed.
            # 2. FK violation — the user was deleted between auth check and INSERT.
            #    Roll back and re-fetch returns None; raise 404 in that case.
            await self.db.rollback()
            profile = await self.repo.get_by_user_id(user_id)
            if profile is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="USER_NOT_FOUND",
                ) from None
            return profile

    async def get_profile_by_id(self, profile_id: int) -> Profile:
        profile = await self.repo.get_profile_by_id(profile_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PROFILE_NOT_FOUND",
            ) from None
        return profile

    async def update_profile(self, user_id: int, profile_data: ProfileUpdate) -> Profile:
        profile = await self.repo.get_by_user_id(user_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PROFILE_NOT_FOUND",
            ) from None
        return await self.repo.update_profile(user_id, profile_data)

    async def get_safe_profile(self, user_id: int) -> Profile:
        profile = await self.repo.get_safe_profile(user_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PROFILE_NOT_FOUND",
            ) from None
        return profile
