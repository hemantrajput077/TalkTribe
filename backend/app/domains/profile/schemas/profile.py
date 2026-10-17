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
    name: str | None = None
    bio: str | None = None
    profession: str | None = None
    location: str | None = None
    avatar_url: str | None = None
    native_language: str | None = None
    english_level: str | None = None
    learning_language: str | None = None
    interests: list[str] = []
