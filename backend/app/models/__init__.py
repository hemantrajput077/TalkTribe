"""
Models package.

Import all models here so Alembic can detect them for migrations.
"""

from app.models.auth import User
from app.models.otp import Otp
from app.models.refresh_token import RefreshToken

__all__ = ["User", "RefreshToken", "Otp"]
