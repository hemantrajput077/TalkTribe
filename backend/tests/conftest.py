"""
conftest.py — Test configuration and shared fixtures.

Sets required env vars BEFORE any app module is imported (pydantic-settings
reads them at import time). All auth endpoint tests use:
  - SQLite in-memory database  (no PostgreSQL needed)
  - Mocked email sending        (no SMTP server needed)
  - Mocked Redis operations     (no Redis server needed)
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_ci.db")
os.environ.setdefault("SECRET_KEY", "ci-test-secret-key-at-least-32-chars-long!!!")
os.environ.setdefault("REFRESH_SECRET_KEY", "ci-test-refresh-key-at-least-32-chars-long!!")
os.environ.setdefault("JWT_SECRET_KEY", "ci-test-jwt-key-at-least-32-chars-long!!!!!!")

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Import every model so SQLAlchemy registers them under Base.metadata
# before create_all is called.
import app.domains.auth.infrastructure.otp_model  # noqa: F401
import app.domains.auth.infrastructure.token_model  # noqa: F401
import app.domains.auth.infrastructure.user_model  # noqa: F401
import app.domains.profile.infrastructure.interest_model  # noqa: F401
import app.domains.profile.infrastructure.profile_model  # noqa: F401
import app.domains.profile.infrastructure.user_interest_model  # noqa: F401
from app.infrastructure.database.base import Base

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
async def db_session():
    """
    Isolated in-memory SQLite database per test.

    StaticPool shares one connection across the whole session so that
    the test and the app dependency override see the same data.
    Tables are created before the test and dropped after.
    """
    engine = create_async_engine(
        _TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
def mock_send_email():
    """
    Replaces send_otp_email with an AsyncMock that returns True.
    Tests that need the OTP value can read it from mock_send_email.call_args[0][1]
    (second positional argument — the OTP string passed by the route).
    """
    with patch(
        "app.domains.auth.api.routes.send_otp_email",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = True
        yield mock


@pytest.fixture()
async def client(db_session, mock_send_email):
    """
    Full async HTTP test client.

    Wires up:
      - in-memory SQLite via get_db override
      - mocked Redis startup/shutdown (lifespan)
      - mocked is_blocklisted (always returns False)
      - mocked blocklist_token (no-op)
      - mocked send_otp_email (via mock_send_email fixture)
    """
    from app.infrastructure.database.dependencies import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("app.infrastructure.cache.redis.startup", new_callable=AsyncMock),
        patch("app.infrastructure.cache.redis.shutdown", new_callable=AsyncMock),
        patch(
            "app.api.dependencies.is_blocklisted",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "app.domains.auth.application.auth_service.blocklist_token",
            new_callable=AsyncMock,
        ),
        # Rate-limit functions are no-ops by default so existing tests are unaffected.
        # Individual rate-limit tests override these with nested patches.
        patch("app.domains.auth.api.routes.check_register_rate_limit", new_callable=AsyncMock),
        patch("app.domains.auth.api.routes.check_login_rate_limit", new_callable=AsyncMock),
        patch("app.domains.auth.api.routes.check_verify_email_rate_limit", new_callable=AsyncMock),
        patch("app.domains.auth.api.routes.check_resend_otp_rate_limit", new_callable=AsyncMock),
        patch("app.domains.auth.api.routes.acquire_resend_otp_cooldown", new_callable=AsyncMock),
        patch("app.domains.auth.api.routes.release_resend_otp_cooldown", new_callable=AsyncMock),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


# ── Reusable payload ──────────────────────────────────────────────────────────

VALID_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "phone_number": "+919876543210",
    "password": "SecurePass1!",
    "full_name": "Test User",
}

# ── Interests seed fixture ─────────────────────────────────────────────────────

_SEED_INTERESTS = [
    {"id": 1, "name": "Art"},
    {"id": 2, "name": "Books"},
    {"id": 3, "name": "Business"},
    {"id": 4, "name": "Cooking"},
    {"id": 5, "name": "Fashion"},
    {"id": 6, "name": "Fitness"},
    {"id": 7, "name": "Gaming"},
    {"id": 8, "name": "Movies"},
    {"id": 9, "name": "Music"},
    {"id": 10, "name": "Nature"},
    {"id": 11, "name": "Science"},
    {"id": 12, "name": "Sports"},
    {"id": 13, "name": "Technology"},
    {"id": 14, "name": "Travel"},
]


@pytest.fixture()
async def seed_interests(db_session):
    """
    Insert the 14 predefined interests into the in-memory SQLite test DB.

    Use this fixture in any test that calls GET /interests or PUT /profiles/me/interests
    so that valid interest IDs are available without running Alembic migrations.
    """
    from app.domains.profile.infrastructure.interest_model import Interest

    db_session.add_all([Interest(id=row["id"], name=row["name"]) for row in _SEED_INTERESTS])
    await db_session.commit()
