from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.infrastructure.config.config import settings

MAX_INTERESTS = settings.MAX_INTERESTS
_MAX_CUSTOM_NAME_LEN = 50


# ── Read models ───────────────────────────────────────────────────────────────


class InterestResponse(BaseModel):
    """A single interest (predefined or custom)."""

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
    - interest_ids: IDs from the predefined catalogue. Duplicates are removed.
    - custom_interests: Free-text names. Each is trimmed; empty strings, names
      over 50 chars, and within-request duplicates (case-insensitive) are
      rejected. Names matching a predefined interest are rejected by the service.
    - Combined total of unique interest_ids + unique custom_interests must not
      exceed MAX_INTERESTS (10).
    - An empty body ({}) or both fields empty clears all interests.
    """

    interest_ids: list[int] = []
    custom_interests: list[str] = []

    @field_validator("interest_ids")
    @classmethod
    def deduplicate_ids(cls, v: list[int]) -> list[int]:
        seen: set[int] = set()
        return [x for x in v if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]

    @field_validator("custom_interests")
    @classmethod
    def validate_custom_names(cls, v: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen_normalised: set[str] = set()

        for raw in v:
            name = raw.strip()
            if not name:
                raise ValueError("Custom interest names must not be empty or whitespace.")
            if len(name) > _MAX_CUSTOM_NAME_LEN:
                raise ValueError(
                    f"Custom interest names must be {_MAX_CUSTOM_NAME_LEN} characters or fewer."
                )
            normalised = name.lower()
            if normalised in seen_normalised:
                continue  # silently deduplicate within the request
            seen_normalised.add(normalised)
            cleaned.append(name)

        return cleaned

    @model_validator(mode="after")
    def combined_count_within_limit(self) -> UpdateInterestsRequest:
        total = len(self.interest_ids) + len(self.custom_interests)
        if total > MAX_INTERESTS:
            raise ValueError(
                f"You can select at most {MAX_INTERESTS} interests in total "
                f"(interest_ids + custom_interests combined)."
            )
        return self


class UpdateInterestsResponse(BaseModel):
    """Response body for PUT /api/v1/profiles/me/interests."""

    interests: list[InterestResponse]
