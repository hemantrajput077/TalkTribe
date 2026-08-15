"""
Models package.

Import all models here so Alembic can detect them for migrations.
"""

from app.models.auth import User
from app.models.refresh_token import RefreshToken
from app.models.otp import Otp

__all__ = ["User", "RefreshToken", "Otp"]
