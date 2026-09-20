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

    async def get_by_code(self, code: str) -> Language | None:
        result = await self.db.execute(select(Language).where(Language.code == code))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Language | None:
        result = await self.db.execute(select(Language).where(Language.name == name))
        return result.scalar_one_or_none()

    async def create(self, name: str, code: str) -> Language:
        language = Language(name=name, code=code)
        self.db.add(language)
        await self.db.commit()
        await self.db.refresh(language)
        return language
