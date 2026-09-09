from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profile.infrastructure.profile_model import Profile
from app.domains.profile.infrastructure.profile_repository import ProfileRepository


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
            # Two concurrent requests from the same new user both saw no profile
            # and both tried to INSERT. The UNIQUE constraint on user_id made the
            # second one fail. Roll back and re-fetch the row the first request created.
            await self.db.rollback()
            profile = await self.repo.get_by_user_id(user_id)
            assert profile is not None  # guaranteed: the other request just created it
            return profile
