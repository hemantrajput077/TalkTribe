from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profile.infrastructure.interest_model import Interest
from app.domains.profile.infrastructure.interest_repository import InterestRepository


class InterestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = InterestRepository(db)

    async def list_interests(self) -> list[Interest]:
        """Return the active predefined interest catalogue, sorted by name."""
        return await self.repo.get_all()

    async def get_user_interests(self, user_id: int) -> list[Interest]:
        """Return the interests currently selected by the given user."""
        return await self.repo.get_user_interests(user_id)

    async def set_user_interests(
        self,
        user_id: int,
        interest_ids: list[int],
        custom_interests: list[str],
    ) -> list[Interest]:
        """
        Validate then replace a user's interest selections.

        Predefined IDs:
          - Raises HTTP 422 if any submitted ID does not exist in the catalogue.

        Custom interest names (already trimmed and deduped by the schema):
          - Raises HTTP 422 if the name (normalised to lowercase) matches any
            existing predefined interest — use interest_ids for those instead.
          - Reuses an existing custom interest row if the normalised name matches.
          - Creates a new row (is_predefined=False) if the name is new.

        Returns the saved Interest objects for response serialisation.
        """
        all_ids: list[int] = list(interest_ids)

        # ── Validate predefined IDs ───────────────────────────────────────────
        if interest_ids:
            found = await self.repo.get_by_ids(interest_ids)
            found_ids = {interest.id for interest in found}
            invalid = set(interest_ids) - found_ids
            if invalid:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"INVALID_INTEREST_ID: {sorted(invalid)}",
                )

        # ── Resolve custom interests ──────────────────────────────────────────
        for display_name in custom_interests:
            normalised = display_name.lower()
            existing = await self.repo.find_by_normalised_name(normalised)

            if existing is not None:
                if existing.is_predefined:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=f"CUSTOM_INTEREST_CONFLICTS_WITH_CATALOGUE: '{display_name}' "
                        f"already exists as a predefined interest. "
                        f"Use interest_ids instead.",
                    )
                # Reuse the existing custom interest row.
                if existing.id not in all_ids:
                    all_ids.append(existing.id)
            else:
                interest = await self.repo.create_custom_interest(display_name, user_id)
                all_ids.append(interest.id)

        return await self.repo.replace_user_interests(user_id, all_ids)
