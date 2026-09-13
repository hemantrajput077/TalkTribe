from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profile.infrastructure.interest_model import Interest
from app.domains.profile.infrastructure.user_interest_model import UserInterest


class InterestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> list[Interest]:
        """Return every predefined interest, sorted alphabetically."""
        result = await self.db.execute(select(Interest).order_by(Interest.name))
        return list(result.scalars().all())

    async def get_by_ids(self, ids: list[int]) -> list[Interest]:
        """
        Return Interest rows whose IDs are in the given list.

        Used by the service to validate that every submitted ID exists in the
        catalogue before saving. If len(returned) < len(ids), some IDs are invalid.
        """
        if not ids:
            return []
        result = await self.db.execute(select(Interest).where(Interest.id.in_(ids)))
        return list(result.scalars().all())

    async def replace_user_interests(self, user_id: int, interest_ids: list[int]) -> list[Interest]:
        """
        Replace all interest selections for a user atomically.

        Steps (single transaction):
          1. DELETE all existing user_interests rows for user_id.
          2. INSERT new rows for each interest_id.
          3. Fetch and return the saved Interest objects.

        An empty interest_ids list clears all selections.
        """
        # Step 1 — delete current selections
        await self.db.execute(delete(UserInterest).where(UserInterest.user_id == user_id))

        # Step 2 — insert new selections
        if interest_ids:
            new_rows = [UserInterest(user_id=user_id, interest_id=iid) for iid in interest_ids]
            self.db.add_all(new_rows)

        await self.db.commit()

        # Step 3 — return the saved Interest objects (for response serialisation)
        return await self.get_by_ids(interest_ids)
