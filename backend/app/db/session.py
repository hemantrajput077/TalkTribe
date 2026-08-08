"""
Re-export SessionLocal for use as a type annotation in route signatures.

Usage in routes:
    def some_route(db: SessionLocal = Depends(get_db)):
        ...
"""

from app.db.database import SessionLocal

__all__ = ["SessionLocal"]
