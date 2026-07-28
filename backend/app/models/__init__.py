"""
Models package.

Import all models here so Alembic can detect them for migrations.
"""

from app.models.auth import User

__all__ = ["User"]
