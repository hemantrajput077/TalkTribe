from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str


class CreateLanguageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=2, max_length=10)
