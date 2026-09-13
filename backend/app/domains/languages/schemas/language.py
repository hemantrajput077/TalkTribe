from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
