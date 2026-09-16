"""
Language routes.

  GET  /languages  → list all supported languages (no auth required)
  POST /languages  → add a new language (admin only)
"""

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.domains.auth.schemas.identity import AuthenticatedIdentity
from app.domains.languages.application.language_service import LanguageService
from app.domains.languages.schemas.language import CreateLanguageRequest, LanguageResponse
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


@router.post(
    "",
    response_model=LanguageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new language (admin only)",
)
async def create_language(
    body: CreateLanguageRequest = Body(...),
    _: AuthenticatedIdentity = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> LanguageResponse:
    svc = LanguageService(db)
    language = await svc.create_language(name=body.name, code=body.code)
    return LanguageResponse.model_validate(language)
