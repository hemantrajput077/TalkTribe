from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_identity
from app.domains.auth.schemas.identity import AuthenticatedIdentity
from app.domains.matching.application.matching_service import MAX_CANDIDATES, MatchingService
from app.domains.matching.schemas.match import MatchListResponse
from app.infrastructure.database.dependencies import get_db

router = APIRouter(prefix="/matches", tags=["matching"])


@router.get(
    "",
    response_model=MatchListResponse,
    summary="Discover compatible English-practice partners",
)
async def get_matches(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(
        default=MAX_CANDIDATES,
        ge=1,
        le=MAX_CANDIDATES,
        description="Maximum candidates to return. Server cap is 20.",
    ),
) -> MatchListResponse:
    svc = MatchingService(db=db)
    return await svc.get_matches(requester_id=identity.user_id, limit=limit)
