from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profile.infrastructure.profile_repository import ProfileRepository
from app.domains.profile.infrastructure.user_language_repository import UserLanguageRepository
from app.domains.profile.schemas.eligibility import IneligibilityReason, ProfileEligibilityResult


class ProfileEligibilityService:
    """Internal service contract for Matching and Pairing domains.

    Determines whether a user's profile is complete enough to participate in
    matching or pairing sessions. A profile is eligible when:
      1. It has a non-empty bio.
      2. It has at least one configured LEARNING language.
    """

    def __init__(
        self,
        db: AsyncSession,
        profile_repo: ProfileRepository | None = None,
        user_lang_repo: UserLanguageRepository | None = None,
    ) -> None:
        self.db = db
        self.profile_repo = profile_repo or ProfileRepository(db)
        self.user_lang_repo = user_lang_repo or UserLanguageRepository(db)

    async def check(self, user_id: int) -> ProfileEligibilityResult:
        """Check if user_id satisfies profile completeness requirements."""
        profile = await self.profile_repo.get_by_user_id(user_id)
        if profile is None or not profile.bio or not profile.bio.strip():
            return ProfileEligibilityResult(
                eligible=False,
                reason=IneligibilityReason.PROFILE_BIO_MISSING,
            )

        has_learning = await self.user_lang_repo.has_learning_language(user_id)
        if not has_learning:
            return ProfileEligibilityResult(
                eligible=False,
                reason=IneligibilityReason.PROFILE_LEARNING_LANGUAGE_MISSING,
            )

        return ProfileEligibilityResult(eligible=True)
