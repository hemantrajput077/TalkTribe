"""
Interest routes.

  GET  /interests                   → list all predefined interests (no auth)
  PUT  /profiles/me/interests       → replace the authenticated user's selections
"""

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_identity
from app.domains.auth.schemas.identity import AuthenticatedIdentity
from app.domains.profile.application.interest_service import InterestService
from app.domains.profile.schemas.interest import (
    InterestListResponse,
    InterestResponse,
    UpdateInterestsRequest,
    UpdateInterestsResponse,
)
from app.infrastructure.database.dependencies import get_db

# ── GET /interests ─────────────────────────────────────────────────────────────

interests_router = APIRouter(prefix="/interests", tags=["interests"])


@interests_router.get(
    "",
    response_model=InterestListResponse,
    summary="List all predefined interests",
)
async def list_interests(db: AsyncSession = Depends(get_db)) -> InterestListResponse:
    """Return the full catalogue of selectable interests. No authentication required."""
    svc = InterestService(db)
    interests = await svc.list_interests()
    return InterestListResponse(interests=[InterestResponse.model_validate(i) for i in interests])


# ── PUT /profiles/me/interests ─────────────────────────────────────────────────

profiles_interests_router = APIRouter(prefix="/profiles", tags=["interests"])


@profiles_interests_router.get(
    "/me/interests",
    response_model=UpdateInterestsResponse,
    summary="Get the authenticated user's selected interests",
)
async def get_my_interests(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> UpdateInterestsResponse:
    """Return the list of interests currently selected by the authenticated user."""
    svc = InterestService(db)
    interests = await svc.get_user_interests(identity.user_id)
    return UpdateInterestsResponse(
        interests=[InterestResponse.model_validate(i) for i in interests]
    )


@profiles_interests_router.put(
    "/me/interests",
    response_model=UpdateInterestsResponse,
    summary="Replace the authenticated user's interest selections",
)
async def set_my_interests(
    body: UpdateInterestsRequest = Body(...),
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> UpdateInterestsResponse:
    """
    Replace all interest selections for the current user (delete-then-insert).

    - Maximum 10 interests total (interest_ids + custom_interests combined).
    - All interest_ids must exist in the predefined catalogue.
    - Custom names matching a predefined interest are rejected (use interest_ids).
    - Submitting both fields empty clears all interests.
    """
    svc = InterestService(db)
    saved = await svc.set_user_interests(
        user_id=identity.user_id,
        interest_ids=body.interest_ids,
        custom_interests=body.custom_interests,
    )
    return UpdateInterestsResponse(interests=[InterestResponse.model_validate(i) for i in saved])
