"""
Profile routes.

  GET /profiles/me  → return the authenticated user's own profile (lazy-create if missing)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_identity
from app.domains.auth.schemas.identity import AuthenticatedIdentity
from app.domains.profile.application.profile_service import ProfileService
from app.domains.profile.schemas.profile import ProfileResponse
from app.infrastructure.database.dependencies import get_db

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get(
    "/me",
    response_model=ProfileResponse,
    summary="Return the authenticated user's own profile",
)
async def get_my_profile(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    svc = ProfileService(db)
    profile = await svc.get_or_create_profile(identity.user_id)
    return ProfileResponse.model_validate(profile)
