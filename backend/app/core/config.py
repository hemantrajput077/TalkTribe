from pydantic_settings import BaseSettings
from pydantic import field_validator
import secrets


class Settings(BaseSettings):
    # ── JWT ────────────────────────────────────────────────────────────────
    SECRET_KEY: str = secrets.token_urlsafe(64)         # access-token key
    REFRESH_SECRET_KEY: str = secrets.token_urlsafe(64) # refresh-token key (separate!)

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15      # short-lived
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./talktribe.db"

    # ── App ────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"               # "production" | "development"

    @field_validator("SECRET_KEY", "REFRESH_SECRET_KEY")
    @classmethod
    def key_must_be_strong(cls, v: str) -> str:
     if len(v) < 32:
        raise ValueError("Secret keys must be at least 32 characters long.")
        return v

    class Config:
        env_file = ".env"


settings = Settings()