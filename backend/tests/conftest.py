"""
conftest.py — pytest configuration and shared fixtures.

Sets required environment variables BEFORE any app module is imported,
so that pydantic-settings does not raise a ValidationError for missing
DATABASE_URL, SECRET_KEY etc.
"""

import os

# Must be set BEFORE importing any app module that instantiates Settings
# These are used by both app/config.py and app/core/config.py
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_ci.db")
os.environ.setdefault("SECRET_KEY", "ci-test-secret-key-at-least-32-chars-long!!!")
os.environ.setdefault("REFRESH_SECRET_KEY", "ci-test-refresh-key-at-least-32-chars-long!!")
os.environ.setdefault("JWT_SECRET_KEY", "ci-test-jwt-key-at-least-32-chars-long!!!!!!")

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture()
async def client():
    """
    Function-scoped async HTTP client for the FastAPI app.

    Uses httpx.AsyncClient with ASGITransport so no real server is started.
    Each test gets a fresh client to avoid scope issues with pytest-asyncio.
    """
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
