from typing import Optional
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator
)
from datetime import datetime



class CreateUser(BaseModel):
    model_config = ConfigDict(
        extra="forbid",          # Reject unknown fields
        str_strip_whitespace=True
    )

    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Username can contain letters, numbers and underscores only."
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be strong."
    )

    full_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if value.lower() in {
            "admin",
            "root",
            "system",
            "support",
            "superuser"
        }:
            raise ValueError("Username is reserved.")

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:

        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter.")

        if not any(c.islower() for c in value):
            raise ValueError("Password must contain at least one lowercase letter.")

        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit.")

        special = "!@#$%^&*()-_=+[]{}|\\:;\"'<>,.?/"
        if not any(c in special for c in value):
            raise ValueError("Password must contain at least one special character.")

        return value

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        if not value.replace(" ", "").isalpha():
            raise ValueError(
                "Full name should contain only alphabetic characters."
            )

        return value.title()

class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str | None = None
    email: EmailStr
    is_active: bool
    created_at: datetime

