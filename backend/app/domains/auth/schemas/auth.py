import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CreateUser(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Username can contain letters, numbers and underscores only.",
    )

    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=15, description = "Phone number must follow E.164 format (e.g., +[CountryCode][Number]). ")
    password: str = Field(..., min_length=8, max_length=128, description="Password must be strong.")

    full_name: str | None = Field(default=None, min_length=2, max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if value.lower() in {"admin", "root", "system", "support", "superuser"}:
            raise ValueError("Username is reserved.")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return value.lower()
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls,value : str) -> str:
        value = value.strip()

        if not re.fullmatch(r"\+[1-9]\d{7,14}",value):
            raise ValueError(
                "Phone number must be in E.164 format , e.g. +919876543210"
            )
        return value

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
    def validate_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.replace(" ", "").isalpha():
            raise ValueError("Full name should contain only alphabetic characters.")
        return value.title()


class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str | None = None
    email: EmailStr
    phone_number : str
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Username can contain letters, numbers and underscores only.",
    )

    password: str = Field(..., min_length=8, max_length=128, description="User password.")

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        reserved = {"admin", "root", "system", "support", "superuser"}
        if value.lower() in reserved:
            raise ValueError("Username is reserved.")
        return value
