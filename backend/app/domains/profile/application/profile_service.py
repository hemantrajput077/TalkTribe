from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.domain.enums import AccountStatus
from app.domains.auth.infrastructure.user_model import User
from app.domains.languages.domain.enums import LanguageRole
from app.domains.profile.infrastructure.interest_model import Interest
from app.domains.profile.infrastructure.profile_model import Profile
from app.domains.profile.infrastructure.profile_repository import ProfileRepository
from app.domains.profile.infrastructure.user_interest_model import UserInterest
from app.domains.profile.infrastructure.user_language_model import UserLanguage
from app.domains.profile.schemas.profile import PeerProfileResponse, ProfileUpdate


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

    async def get_safe_profile_full(self, user_id: int) -> PeerProfileResponse | None:
        user_res = await self.db.execute(
            select(User, Profile)
            .join(Profile, Profile.user_id == User.id, isouter=True)
            .where(User.id == user_id, User.account_status == AccountStatus.ACTIVE)
        )
        row = user_res.first()
        if not row:
            return None
        user, profile = row

        # Fetch languages
        lang_res = await self.db.execute(
            select(UserLanguage).where(UserLanguage.user_id == user_id)
        )
        user_langs = list(lang_res.scalars().all())
        native = next(
            (lang.language_name for lang in user_langs if lang.role == LanguageRole.NATIVE),
            "English",
        )
        learning = next((lang for lang in user_langs if lang.role == LanguageRole.LEARNING), None)

        # Fetch interests
        int_res = await self.db.execute(
            select(Interest.name)
            .join(UserInterest, UserInterest.interest_id == Interest.id)
            .where(UserInterest.user_id == user_id)
        )
        interest_names = list(int_res.scalars().all())

        return PeerProfileResponse(
            user_id=user.id,
            name=user.full_name or user.username,
            bio=profile.bio if profile else None,
            profession=profile.profession if profile else None,
            location=profile.location if profile else None,
            avatar_url=profile.avatar_url if profile else None,
            native_language=native,
            learning_language=learning.language_name if learning else "English",
            english_level=learning.proficiency if learning else "Intermediate",
            interests=interest_names,
        )

    async def list_active_profiles(
        self, exclude_user_id: int | None = None, limit: int = 50
    ) -> list[PeerProfileResponse]:
        query = (
            select(User, Profile)
            .join(Profile, Profile.user_id == User.id, isouter=True)
            .where(User.account_status == AccountStatus.ACTIVE, User.is_active == True)  # noqa: E712
        )
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        query = query.limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        profiles: list[PeerProfileResponse] = []
        for user, profile in rows:
            lang_res = await self.db.execute(
                select(UserLanguage).where(UserLanguage.user_id == user.id)
            )
            user_langs = list(lang_res.scalars().all())
            native = next(
                (lang.language_name for lang in user_langs if lang.role == LanguageRole.NATIVE),
                "English",
            )
            learning = next(
                (lang for lang in user_langs if lang.role == LanguageRole.LEARNING), None
            )

            int_res = await self.db.execute(
                select(Interest.name)
                .join(UserInterest, UserInterest.interest_id == Interest.id)
                .where(UserInterest.user_id == user.id)
            )
            interest_names = list(int_res.scalars().all())

            profiles.append(
                PeerProfileResponse(
                    user_id=user.id,
                    name=user.full_name or user.username,
                    bio=profile.bio if profile else None,
                    profession=profile.profession if profile else None,
                    location=profile.location if profile else None,
                    avatar_url=profile.avatar_url if profile else None,
                    native_language=native,
                    learning_language=learning.language_name if learning else "English",
                    english_level=learning.proficiency if learning else "Intermediate",
                    interests=interest_names,
                )
            )

        return profiles
