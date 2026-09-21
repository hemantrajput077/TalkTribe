from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profile.infrastructure.interest_model import Interest
from app.domains.profile.infrastructure.user_interest_model import UserInterest


class InterestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> list[Interest]:
        """Return every active predefined interest, sorted alphabetically."""
        result = await self.db.execute(
            select(Interest)
            .where(Interest.is_predefined == True, Interest.is_active == True)  # noqa: E712
            .order_by(Interest.name)
        )
        return list(result.scalars().all())

    async def get_by_ids(self, ids: list[int]) -> list[Interest]:
        """Return Interest rows whose IDs are in the given list."""
        if not ids:
            return []
        result = await self.db.execute(select(Interest).where(Interest.id.in_(ids)))
        return list(result.scalars().all())

    async def find_by_normalised_name(self, normalised: str) -> Interest | None:
        """Case-insensitive lookup by name. Returns None if not found."""
        result = await self.db.execute(
            select(Interest).where(func.lower(Interest.name) == normalised)
        )
        return result.scalar_one_or_none()

    async def create_custom_interest(self, display_name: str, user_id: int) -> Interest:
        """
        Persist a new user-created interest and flush to obtain its ID.

        Does NOT commit — the caller (service) owns the transaction boundary.
        """
        interest = Interest(
            name=display_name,
            is_predefined=False,
            created_by_user_id=user_id,
            is_active=True,
        )
        self.db.add(interest)
        await self.db.flush()
        await self.db.refresh(interest)
        return interest

    async def get_user_interests(self, user_id: int) -> list[Interest]:
        """Return the interests currently selected by the given user, sorted by name."""
        result = await self.db.execute(
            select(Interest)
            .join(UserInterest, UserInterest.interest_id == Interest.id)
            .where(UserInterest.user_id == user_id)
            .order_by(Interest.name)
        )
        return list(result.scalars().all())

    async def replace_user_interests(self, user_id: int, interest_ids: list[int]) -> list[Interest]:
        """
        Replace all interest selections for a user atomically.

        Steps (single transaction):
          1. DELETE all existing user_interests rows for user_id.
          2. INSERT new rows for each interest_id.
          3. Fetch and return the saved Interest objects.
        """
        await self.db.execute(delete(UserInterest).where(UserInterest.user_id == user_id))

        if interest_ids:
            new_rows = [UserInterest(user_id=user_id, interest_id=iid) for iid in interest_ids]
            self.db.add_all(new_rows)

        await self.db.commit()

        return await self.get_by_ids(interest_ids)
