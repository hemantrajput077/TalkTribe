"""
Models package.

Import all models here so Alembic can detect them for migrations.
"""

from app.domains.auth.infrastructure.user_model import User
from app.domains.auth.infrastructure.otp_model import Otp
from app.domains.auth.infrastructure.token_model import RefreshToken

__all__ = ["User", "RefreshToken", "Otp"]
