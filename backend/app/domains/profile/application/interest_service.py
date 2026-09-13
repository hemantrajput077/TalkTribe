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
        """Return the full predefined interest catalogue, sorted by name."""
        return await self.repo.get_all()

    async def get_user_interests(self, user_id: int) -> list[Interest]:
        """Return the interests currently selected by the given user."""
        return await self.repo.get_user_interests(user_id)

    async def set_user_interests(self, user_id: int, interest_ids: list[int]) -> list[Interest]:
        """
        Validate then replace a user's interest selections.

        Raises HTTP 422 if any submitted ID does not exist in the catalogue.
        Returns the saved Interest objects for response serialisation.
        """
        if interest_ids:
            found = await self.repo.get_by_ids(interest_ids)
            found_ids = {interest.id for interest in found}
            invalid = set(interest_ids) - found_ids
            if invalid:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"INVALID_INTEREST_ID: {sorted(invalid)}",
                )

        return await self.repo.replace_user_interests(user_id, interest_ids)
