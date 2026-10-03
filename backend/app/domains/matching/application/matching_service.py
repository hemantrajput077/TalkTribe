from __future__ import annotations
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.languages.domain.enums import LanguageRole
from app.domains.matching.application.profile_matching_reader import ProfileMatchingReader
from app.domains.matching.application.scoring_engine import score_candidate
from app.domains.matching.contracts.interaction_eligibility import (
    InteractionEligibility,
    NullInteractionEligibility,
)
from app.domains.matching.schemas.match import MatchCandidateResponse, MatchListResponse
from app.domains.profile.application.profile_eligibility_service import ProfileEligibilityService
from app.domains.profile.infrastructure.profile_repository import ProfileRepository
from app.domains.profile.infrastructure.user_language_repository import UserLanguageRepository

MAX_CANDIDATES: int = 20


class MatchingService:
    def __init__(
        self,
        db: AsyncSession,
        interaction_eligibility: InteractionEligibility | None = None,
    ) -> None:
        self.db = db
        self._profile_eligibility = ProfileEligibilityService(
            db=db,
            profile_repo=ProfileRepository(db),
            user_lang_repo=UserLanguageRepository(db),
        )
        self._interaction_eligibility: InteractionEligibility = (
            interaction_eligibility or NullInteractionEligibility()
        )
        self._reader = ProfileMatchingReader(db)
        self._lang_repo = UserLanguageRepository(db)

    async def get_matches(
        self,
        requester_id: int,
        limit: int = MAX_CANDIDATES,
    ) -> MatchListResponse:
        effective_limit = min(limit, MAX_CANDIDATES)

        # 1. Requester eligibility check (PROF-06)
        requester_result = await self._profile_eligibility.check(requester_id)
        if not requester_result.eligible:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(requester_result.reason),
            )

        # 2. Load requester scoring inputs
        requester_interest_ids = await self._reader.get_requester_interest_ids(requester_id)
        requester_profession = await self._reader.get_requester_profession(requester_id)
        requester_languages = await self._lang_repo.get_by_user_id(requester_id)
        requester_proficiency: str | None = next(
            (ul.proficiency for ul in requester_languages if ul.role == LanguageRole.LEARNING),
            None,
        )

        # 3. Discover raw candidate IDs
        raw_candidate_ids = await self._reader.get_eligible_candidate_ids(
            exclude_user_id=requester_id,
        )

        # 4. Filter by profile completeness (PROF-06)
        profile_eligible_ids: list[int] = []
        for cid in raw_candidate_ids:
            result = await self._profile_eligibility.check(cid)
            if result.eligible:
                profile_eligible_ids.append(cid)

        # 5. Filter by interaction eligibility (BLOCK-01)
        interaction_eligible_ids: list[int] = []
        for cid in profile_eligible_ids:
            if await self._interaction_eligibility.are_interaction_eligible(requester_id, cid):
                interaction_eligible_ids.append(cid)

        if not interaction_eligible_ids:
            return MatchListResponse(items=[], count=0)

        # 6. Batch-load candidate data
        summaries = await self._reader.get_candidate_summaries(interaction_eligible_ids)

        # 7. Score
        scored = [
            (
                score_candidate(
                    requester_interest_ids=requester_interest_ids,
                    requester_profession=requester_profession,
                    requester_proficiency=requester_proficiency,
                    candidate=summary,
                ),
                summary,
            )
            for summary in summaries
        ]

        # 8. Rank: descending score, ascending user_id as stable tie-breaker
        scored.sort(key=lambda pair: (-pair[0], pair[1].user_id))

        # 9. Limit
        top = scored[:effective_limit]

        # 10. Build response
        items: list[MatchCandidateResponse] = []
        for compatibility_score, summary in top:
            shared_interest_names = sorted(
                summary.interest_names[iid]
                for iid in (requester_interest_ids & summary.interest_ids)
                if iid in summary.interest_names
            )
            items.append(
                MatchCandidateResponse(
                    user_id=summary.user_id,
                    display_name=summary.display_name,
                    profile_photo_url=summary.avatar_url,
                    proficiency_level=summary.proficiency_level,
                    shared_interests=shared_interest_names,
                    profession=summary.profession,
                    compatibility_score=compatibility_score,
                )
            )

        return MatchListResponse(items=items, count=len(items))
