"""
Sync SQLAlchemy engine and session factory.

Uses psycopg2 (sync) driver for PostgreSQL.
DATABASE_URL format: postgresql://user:password@host:port/dbname
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,           # Set to False in production
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)
