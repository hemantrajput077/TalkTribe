from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings
from app.db.base import Base  # single Base shared by all models and Alembic

"""
Database configuration and session management.

Uses SQLAlchemy 2.0+ async engine for non-blocking database operations.
"""

# Create async engine
# echo=True shows SQL queries in console (useful for learning/debugging)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Number of connections to keep open
    max_overflow=20,  # Additional connections when pool is full
)

# Create async session factory
# expire_on_commit=False prevents attributes from being expired after commit
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Dependency for FastAPI routes
async def get_db() -> AsyncSession:
    """
    Dependency that provides a database session to route handlers.

    Automatically commits on success, rolls back on error, and closes the session.

    Usage in routes:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
