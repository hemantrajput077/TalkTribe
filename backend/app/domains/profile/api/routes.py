"""
Profile routes.

  GET  /profiles/me           → return the authenticated user's own profile (lazy-create if missing)
  PATCH /profiles/me          → update the authenticated user's own profile
  PUT  /profiles/me/languages → replace the authenticated user's full language configuration
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_identity, require_admin
from app.domains.auth.schemas.identity import AuthenticatedIdentity
from app.domains.profile.application.profile_service import ProfileService
from app.domains.profile.application.user_language_service import UserLanguageService
from app.domains.profile.schemas.profile import PeerProfileResponse, ProfileResponse, ProfileUpdate
from app.domains.profile.schemas.user_language import (
    PutLanguagesRequest,
    PutLanguagesResponse,
    UserLanguageOut,
)
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
    "/admin/{profile_id}",
    response_model=ProfileResponse,
    summary="Get a profile by user ID (Admin only)",
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


@router.put(
    "/me/languages",
    response_model=PutLanguagesResponse,
    summary="Replace the authenticated user's full language configuration",
)
async def put_my_languages(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    data: PutLanguagesRequest = Body(...),
    db: AsyncSession = Depends(get_db),
) -> PutLanguagesResponse:
    svc = UserLanguageService(db)
    user_languages = await svc.replace_user_languages(identity.user_id, data)
    return PutLanguagesResponse(
        languages=[UserLanguageOut.model_validate(ul) for ul in user_languages]
    )


@router.get(
    "/{user_id}", response_model=PeerProfileResponse, summary="View another user's profile"
)
async def get_safe_profile(
    user_id: int = Path(..., title="The ID of the user whose profile to retrieve"),
    auth: AuthenticatedIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    svc = ProfileService(db)
    profile = await svc.get_safe_profile(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PROFILE_NOT_FOUND",
        ) from None
    return PeerProfileResponse.model_validate(profile)
