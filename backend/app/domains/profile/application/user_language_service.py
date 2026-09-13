from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.languages.infrastructure.language_repository import LanguageRepository
from app.domains.profile.infrastructure.user_language_model import UserLanguage
from app.domains.profile.infrastructure.user_language_repository import UserLanguageRepository
from app.domains.profile.schemas.user_language import PutLanguagesRequest


class UserLanguageService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserLanguageRepository(db)
        self.lang_repo = LanguageRepository(db)

    async def replace_user_languages(
        self, user_id: int, data: PutLanguagesRequest
    ) -> list[UserLanguage]:
        submitted_ids = [entry.language_id for entry in data.languages]
        found = await self.lang_repo.get_by_ids(submitted_ids)
        found_ids = {lang.id for lang in found}

        missing = set(submitted_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Language IDs not found: {sorted(missing)}",
            )

        return await self.repo.replace_all(user_id, data.languages)
