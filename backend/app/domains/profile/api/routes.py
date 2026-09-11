"""
Profile routes.

  GET /profiles/me  → return the authenticated user's own profile (lazy-create if missing)
"""

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_identity, require_admin
from app.domains.auth.schemas.identity import AuthenticatedIdentity
from app.domains.profile.application.profile_service import ProfileService
from app.domains.profile.schemas.profile import ProfileResponse, ProfileUpdate
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


@router.patch(
    "/me",
    response_model=ProfileResponse,
    summary="Update the authenticated user's own profile",
)
async def update_my_profile(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    profile_data: ProfileUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    svc = ProfileService(db)
    profile = await svc.update_profile(identity.user_id, profile_data)
    return ProfileResponse.model_validate(profile)


@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Get a profile by user ID",
    response_description="The profile with the specified user ID",
)
async def get_profile_by_id(
    profile_id: int = Path(..., title="The ID of the profile to retrieve"),
    identity: AuthenticatedIdentity = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    svc = ProfileService(db)
    profile = await svc.get_profile_by_id(profile_id)
    return ProfileResponse.model_validate(profile)
