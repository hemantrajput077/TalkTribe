"""
Language routes.

  GET /languages  → list all supported languages (no auth required)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.languages.application.language_service import LanguageService
from app.domains.languages.schemas.language import LanguageResponse
from app.infrastructure.database.dependencies import get_db

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get(
    "",
    response_model=list[LanguageResponse],
    summary="List all supported languages",
)
async def list_languages(
    db: AsyncSession = Depends(get_db),
) -> list[LanguageResponse]:
    svc = LanguageService(db)
    languages = await svc.list_languages()
    return [LanguageResponse.model_validate(lang) for lang in languages]
