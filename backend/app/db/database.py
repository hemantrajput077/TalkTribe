"""
Async SQLAlchemy engine — used only by app.db.session for SessionLocal re-export.

The primary async session factory (get_db dependency) lives in app/database.py.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)

# Async session factory — correct pairing: AsyncEngine + async_sessionmaker
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
