from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    bio: str | None
    profession: str | None
    location: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bio: str | None = Field(default=None, max_length=500)
    profession: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = None


class PeerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    bio: str | None
    profession: str | None
    location: str | None
    avatar_url: str | None
