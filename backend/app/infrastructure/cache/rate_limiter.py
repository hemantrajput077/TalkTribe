"""
Redis-backed rate limiting utilities for TalkTribe.

Provides:
- get_client_ip()        — safe direct-connection IP extractor
- check_rate_limit()     — fixed-window counter via atomic Lua script
- check_cooldown()       — single-use cooldown lock via SET NX EX
- release_cooldown()     — removes a cooldown key to allow immediate retry
"""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from app.infrastructure.cache.redis import get_redis

# Atomically increment the counter and set the TTL on the first call only.
# Subsequent calls within the window do not reset the expiry.
# KEYS[1] — the rate-limit key
# ARGV[1] — window size in seconds (string; Lua tonumber() coerces it)
# Returns  — {count, ttl} as a two-element Redis array
_INCR_WITH_EXPIRE = """\
local n = redis.call('INCR', KEYS[1])
if n == 1 then
    redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1]))
end
return {n, redis.call('TTL', KEYS[1])}
"""


def get_client_ip(request: Request) -> str:
    """
    Return the direct-connection client IP from request.client.host.

    X-Forwarded-For is intentionally NOT read here. The application has no
    reverse proxy configured, so trusting forwarded headers would allow any
    client to spoof its IP and bypass rate limits. If a trusted reverse proxy
    is added later, configure Uvicorn's ProxyHeadersMiddleware in main.py so
    that Starlette resolves the real IP at the transport layer before requests
    reach application code — do not add header-trust logic here.
    """
    if request.client is None:
        return "unknown"
    return request.client.host


async def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    """
    Fixed-window rate limit check backed by Redis.

    Increments the counter for *key*. On the very first increment the
    expiry window is set in the same Lua round-trip (atomic — safe under
    concurrent requests). If the counter exceeds *limit*, raises HTTP 429
    with a Retry-After header derived from the current Redis TTL.
    """
    redis = get_redis()
    result = await redis.eval(_INCR_WITH_EXPIRE, 1, key, str(window_seconds))  # type: ignore[misc]
    count, ttl = int(result[0]), int(result[1])
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AUTH_RATE_LIMIT_EXCEEDED",
            headers={"Retry-After": str(max(ttl, 0))},
        )


async def check_cooldown(key: str, cooldown_seconds: int) -> None:
    """
    Acquire a single-use cooldown lock via SET NX EX (atomic).

    If the key did not exist it is created and the caller may proceed.
    If the key already exists the cooldown period has not elapsed; raises
    HTTP 429 with Retry-After set to the remaining TTL.
    """
    redis = get_redis()
    acquired = await redis.set(key, "1", nx=True, ex=cooldown_seconds)
    if acquired is None:
        ttl = await redis.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AUTH_OTP_RESEND_COOLDOWN",
            headers={"Retry-After": str(max(ttl, 0))},
        )


async def release_cooldown(key: str) -> None:
    """Delete the cooldown key so the caller may retry immediately."""
    await get_redis().delete(key)
