from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.languages.infrastructure.language_model import Language
from app.domains.languages.infrastructure.language_repository import LanguageRepository


class LanguageService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = LanguageRepository(db)

    async def list_languages(self) -> list[Language]:
        return await self.repo.list_all()
