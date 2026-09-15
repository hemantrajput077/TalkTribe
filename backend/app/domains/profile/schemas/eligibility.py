from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class IneligibilityReason(StrEnum):
    PROFILE_BIO_MISSING = "PROFILE_BIO_MISSING"
    PROFILE_LEARNING_LANGUAGE_MISSING = "PROFILE_LEARNING_LANGUAGE_MISSING"


class ProfileEligibilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    eligible: bool
    reason: IneligibilityReason | str | None = None
