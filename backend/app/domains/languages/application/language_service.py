from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.languages.infrastructure.language_model import Language
from app.domains.languages.infrastructure.language_repository import LanguageRepository


class LanguageService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = LanguageRepository(db)

    async def list_languages(self) -> list[Language]:
        return await self.repo.list_all()

    async def create_language(self, name: str, code: str) -> Language:
        normalised_code = code.strip().lower()
        normalised_name = name.strip()

        if await self.repo.get_by_code(normalised_code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="LANGUAGE_CODE_ALREADY_EXISTS",
            )
        if await self.repo.get_by_name(normalised_name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="LANGUAGE_NAME_ALREADY_EXISTS",
            )

        return await self.repo.create(name=normalised_name, code=normalised_code)
