"""
test_app.py — HTTP endpoint tests using the FastAPI test client.

Tests the public endpoints that do NOT require a live database:
- GET /          → welcome message
- GET /health    → health status
- GET /api/v1/ping → ping/pong

These tests import the FastAPI app but do not exercise DB-dependent routes,
so they work in CI without a running PostgreSQL or SQLite setup.
"""

import pytest


@pytest.mark.asyncio
async def test_root(client):
    """Root endpoint returns welcome message."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to TalkTribe API"
    assert "version" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_health_check(client):
    """Health check endpoint returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_ping(client):
    """Ping endpoint returns pong."""
    response = await client.get("/api/v1/ping")
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "pong"}


@pytest.mark.asyncio
async def test_openapi_schema_accessible(client):
    """OpenAPI schema endpoint is reachable (confirms all routes are importable)."""
    response = await client.get("/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert schema["info"]["title"] == "TalkTribe API"
