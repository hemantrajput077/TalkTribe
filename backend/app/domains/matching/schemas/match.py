from __future__ import annotations

"""
Pydantic response schemas for the Matching API (M3).

Response shape matches matching.md §20 exactly:

    {
      "items": [
        {
          "user_id": 123,
          "display_name": "Alice",
          "profile_photo_url": null,
          "proficiency_level": "B1",
          "shared_interests": ["Music", "Photography"],
          "profession": "Developer",
          "compatibility_score": 82
        }
      ],
      "count": 1
    }

Safe-field policy (matching.md §35):
  - No email, phone, password, OTP, refresh tokens, admin notes, or block internals.
"""

from pydantic import BaseModel


class MatchCandidateResponse(BaseModel):
    user_id: int
    display_name: str | None
    profile_photo_url: str | None
    proficiency_level: str | None
    shared_interests: list[str]
    profession: str | None
    compatibility_score: int


class MatchListResponse(BaseModel):
    items: list[MatchCandidateResponse]
    count: int
