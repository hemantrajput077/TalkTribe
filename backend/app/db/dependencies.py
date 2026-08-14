"""
Re-exports the async get_db dependency from app.database.

Any module that still imports `from app.db.dependencies import get_db`
continues to work without changes.
"""

from app.database import get_db

__all__ = ["get_db"]
