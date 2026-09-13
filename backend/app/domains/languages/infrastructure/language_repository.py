from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.languages.infrastructure.language_model import Language


class LanguageRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self) -> list[Language]:
        result = await self.db.execute(select(Language).order_by(Language.name))
        return list(result.scalars().all())

    async def get_by_ids(self, ids: list[int]) -> list[Language]:
        result = await self.db.execute(select(Language).where(Language.id.in_(ids)))
        return list(result.scalars().all())
