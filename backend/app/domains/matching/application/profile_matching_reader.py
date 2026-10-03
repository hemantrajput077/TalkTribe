from __future__ import annotations
from dataclasses import dataclass, field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.auth.domain.enums import AccountStatus
from app.domains.auth.infrastructure.user_model import User
from app.domains.languages.domain.enums import LanguageRole
from app.domains.profile.infrastructure.interest_model import Interest
from app.domains.profile.infrastructure.profile_model import Profile
from app.domains.profile.infrastructure.user_interest_model import UserInterest
from app.domains.profile.infrastructure.user_language_model import UserLanguage


@dataclass
class CandidateSummary:
    user_id: int
    display_name: str | None
    avatar_url: str | None
    profession: str | None
    proficiency_level: str | None
    interest_ids: set[int] = field(default_factory=set)
    interest_names: dict[int, str] = field(default_factory=dict)


class ProfileMatchingReader:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_requester_interest_ids(self, user_id: int) -> set[int]:
        result = await self.db.execute(
            select(UserInterest.interest_id).where(UserInterest.user_id == user_id)
        )
        return set(result.scalars().all())

    async def get_requester_profession(self, user_id: int) -> str | None:
        result = await self.db.execute(
            select(Profile.profession).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_eligible_candidate_ids(self, exclude_user_id: int) -> list[int]:
        result = await self.db.execute(
            select(User.id).where(
                User.id != exclude_user_id,
                User.account_status == AccountStatus.ACTIVE,
                User.is_active == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def get_candidate_summaries(self, user_ids: list[int]) -> list[CandidateSummary]:
        if not user_ids:
            return []

        user_result = await self.db.execute(
            select(User.id, User.full_name, User.username, Profile.avatar_url, Profile.profession)
            .join(Profile, Profile.user_id == User.id, isouter=True)
            .where(User.id.in_(user_ids))
        )
        summaries: dict[int, CandidateSummary] = {}
        for uid, full_name, username, avatar_url, profession in user_result.all():
            summaries[uid] = CandidateSummary(
                user_id=uid,
                display_name=full_name or username,
                avatar_url=avatar_url,
                profession=profession,
                proficiency_level=None,
            )

        interest_result = await self.db.execute(
            select(UserInterest.user_id, Interest.id, Interest.name)
            .join(Interest, Interest.id == UserInterest.interest_id)
            .where(UserInterest.user_id.in_(user_ids))
        )
        for uid, interest_id, interest_name in interest_result.all():
            if uid in summaries:
                summaries[uid].interest_ids.add(interest_id)
                summaries[uid].interest_names[interest_id] = interest_name

        lang_result = await self.db.execute(
            select(UserLanguage.user_id, UserLanguage.proficiency)
            .where(
                UserLanguage.user_id.in_(user_ids),
                UserLanguage.role == LanguageRole.LEARNING,
                UserLanguage.proficiency.isnot(None),
            )
        )
        for uid, proficiency in lang_result.all():
            if uid in summaries and summaries[uid].proficiency_level is None:
                summaries[uid].proficiency_level = proficiency

        return list(summaries.values())
