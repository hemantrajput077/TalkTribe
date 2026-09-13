from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from app.domains.languages.domain.enums import CEFRLevel, LanguageRole


class UserLanguageInput(BaseModel):
    language_id: int
    role: LanguageRole
    proficiency: CEFRLevel | None = None

    @model_validator(mode="after")
    def learning_requires_proficiency(self) -> UserLanguageInput:
        if self.role == LanguageRole.LEARNING and self.proficiency is None:
            raise ValueError("LEARNING language requires a proficiency level")
        return self


class PutLanguagesRequest(BaseModel):
    languages: list[UserLanguageInput]

    @model_validator(mode="after")
    def validate_language_config(self) -> PutLanguagesRequest:
        langs = self.languages

        native_count = sum(1 for lang in langs if lang.role == LanguageRole.NATIVE)
        if native_count != 1:
            raise ValueError(f"Exactly one NATIVE language is required, got {native_count}")

        seen: set[tuple[int, str]] = set()
        for entry in langs:
            key = (entry.language_id, str(entry.role))
            if key in seen:
                raise ValueError(
                    f"Duplicate entry: language_id={entry.language_id}, role={entry.role}"
                )
            seen.add(key)

        native_ids = {lang.language_id for lang in langs if lang.role == LanguageRole.NATIVE}
        learning_ids = {lang.language_id for lang in langs if lang.role == LanguageRole.LEARNING}
        overlap = native_ids & learning_ids
        if overlap:
            raise ValueError(f"Language IDs {sorted(overlap)} cannot be both NATIVE and LEARNING")

        return self


class UserLanguageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language_id: int
    language_name: str
    language_code: str
    role: LanguageRole
    proficiency: CEFRLevel | None


class PutLanguagesResponse(BaseModel):
    languages: list[UserLanguageOut]
