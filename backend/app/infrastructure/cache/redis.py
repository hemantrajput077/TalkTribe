"""
Async Redis client for TalkTribe.

Provides:
- A module-level client instance managed via FastAPI lifespan.
- get_redis() dependency for route/service injection.
- Blocklist helpers used by the auth domain.
"""

from __future__ import annotations

from datetime import UTC, datetime

import redis.asyncio as aioredis

from app.infrastructure.config.config import settings

# Single connection pool shared across the whole process.
# Initialised in startup(), closed in shutdown().
_client: aioredis.Redis | None = None

BLOCKLIST_PREFIX = "blocklist:"


async def startup() -> None:
    global _client
    _client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def shutdown() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None


def get_redis() -> aioredis.Redis:
    if _client is None:
        raise RuntimeError("Redis client is not initialised. Call startup() first.")
    return _client


async def blocklist_token(jti: str, exp: datetime) -> None:
    """Store a token JTI in Redis until it naturally expires."""
    remaining = int((exp.replace(tzinfo=UTC) - datetime.now(UTC)).total_seconds())
    if remaining > 0:
        await get_redis().set(f"{BLOCKLIST_PREFIX}{jti}", "1", ex=remaining)


async def is_blocklisted(jti: str) -> bool:
    """Return True if the JTI is in the blocklist."""
    return await get_redis().exists(f"{BLOCKLIST_PREFIX}{jti}") == 1
