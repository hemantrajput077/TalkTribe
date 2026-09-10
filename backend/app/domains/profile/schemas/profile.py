from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    bio: str | None
    profession: str | None
    location: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime
