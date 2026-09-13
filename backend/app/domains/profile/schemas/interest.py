from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from app.infrastructure.config.config import settings

MAX_INTERESTS = settings.MAX_INTERESTS


# ── Read models ───────────────────────────────────────────────────────────────


class InterestResponse(BaseModel):
    """A single interest from the predefined catalogue."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class InterestListResponse(BaseModel):
    """Response body for GET /api/v1/interests."""

    interests: list[InterestResponse]


# ── Write models ──────────────────────────────────────────────────────────────


class UpdateInterestsRequest(BaseModel):
    """
    Request body for PUT /api/v1/profiles/me/interests.

    Rules:
    - Maximum 10 interest IDs allowed.
    - Duplicate IDs are rejected (Pydantic raises 422 automatically for list uniqueness
      if you use a set, but we keep list for ordered input and deduplicate here).
    - An empty list [] is valid — it clears all interests.
    """

    interest_ids: list[int]

    @field_validator("interest_ids")
    @classmethod
    def max_ten_interests(cls, v: list[int]) -> list[int]:
        # Deduplicate while preserving order
        seen: set[int] = set()
        unique = [x for x in v if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]
        if len(unique) > MAX_INTERESTS:
            raise ValueError(f"You can select at most {MAX_INTERESTS} interests.")
        return unique


class UpdateInterestsResponse(BaseModel):
    """Response body for PUT /api/v1/profiles/me/interests."""

    interests: list[InterestResponse]
