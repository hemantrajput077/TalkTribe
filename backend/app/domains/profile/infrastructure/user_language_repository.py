from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.languages.domain.enums import LanguageRole
from app.domains.profile.infrastructure.user_language_model import UserLanguage
from app.domains.profile.schemas.user_language import UserLanguageInput


class UserLanguageRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def replace_all(
        self, user_id: int, entries: list[UserLanguageInput]
    ) -> list[UserLanguage]:
        await self.db.execute(delete(UserLanguage).where(UserLanguage.user_id == user_id))

        new_rows = [
            UserLanguage(
                user_id=user_id,
                language_id=entry.language_id,
                role=str(entry.role),
                proficiency=str(entry.proficiency) if entry.proficiency else None,
            )
            for entry in entries
        ]
        self.db.add_all(new_rows)
        await self.db.commit()

        result = await self.db.execute(
            select(UserLanguage)
            .where(UserLanguage.user_id == user_id)
            .options(selectinload(UserLanguage.language))
        )
        return list(result.scalars().all())

    async def get_by_user_id(self, user_id: int) -> list[UserLanguage]:
        result = await self.db.execute(
            select(UserLanguage)
            .where(UserLanguage.user_id == user_id)
            .options(selectinload(UserLanguage.language))
        )
        return list(result.scalars().all())

    async def has_learning_language(self, user_id: int) -> bool:
        result = await self.db.execute(
            select(UserLanguage.id)
            .where(
                UserLanguage.user_id == user_id,
                UserLanguage.role == LanguageRole.LEARNING,
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
