"""
Unit tests for the fixed-window rate limiter and cooldown helpers.

Uses fakeredis[lua] so that real Redis semantics (including Lua EVAL) are
exercised without requiring a running Redis server.
"""

import fakeredis
import pytest
from fastapi import HTTPException

import app.infrastructure.cache.rate_limiter as rl


@pytest.fixture
def fake_redis_client(monkeypatch):
    """
    Swap get_redis() for a FakeAsyncRedis instance per test.
    Each test gets a fresh server so state never leaks between tests.
    """
    server = fakeredis.FakeServer()
    client = fakeredis.FakeAsyncRedis(server=server, decode_responses=True)
    monkeypatch.setattr(rl, "get_redis", lambda: client)
    return client


# ── Fixed-window limiter ───────────────────────────────────────────────────────


async def test_first_request_is_allowed(fake_redis_client):
    await rl.check_rate_limit("test:key", limit=3, window_seconds=60)


async def test_requests_up_to_limit_are_allowed(fake_redis_client):
    for _ in range(5):
        await rl.check_rate_limit("test:key", limit=5, window_seconds=60)


async def test_request_above_limit_raises_429(fake_redis_client):
    for _ in range(3):
        await rl.check_rate_limit("test:key", limit=3, window_seconds=60)
    with pytest.raises(HTTPException) as exc_info:
        await rl.check_rate_limit("test:key", limit=3, window_seconds=60)
    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "AUTH_RATE_LIMIT_EXCEEDED"


async def test_retry_after_header_is_present_when_blocked(fake_redis_client):
    for _ in range(3):
        await rl.check_rate_limit("test:key", limit=3, window_seconds=60)
    with pytest.raises(HTTPException) as exc_info:
        await rl.check_rate_limit("test:key", limit=3, window_seconds=60)
    assert "Retry-After" in exc_info.value.headers
    assert int(exc_info.value.headers["Retry-After"]) > 0


async def test_ttl_is_set_on_first_increment(fake_redis_client):
    await rl.check_rate_limit("test:key", limit=5, window_seconds=300)
    ttl = await fake_redis_client.ttl("test:key")
    assert 0 < ttl <= 300


async def test_window_expiry_resets_counter(fake_redis_client):
    for _ in range(2):
        await rl.check_rate_limit("test:key", limit=2, window_seconds=60)
    with pytest.raises(HTTPException):
        await rl.check_rate_limit("test:key", limit=2, window_seconds=60)

    # Simulate window expiry
    await fake_redis_client.delete("test:key")

    # Counter is gone — request should be allowed again
    await rl.check_rate_limit("test:key", limit=2, window_seconds=60)


async def test_each_increment_is_counted(fake_redis_client):
    """Verify the counter advances correctly on each call."""
    for _ in range(7):
        try:
            await rl.check_rate_limit("test:counter", limit=100, window_seconds=60)
        except HTTPException:
            pass
    raw = await fake_redis_client.get("test:counter")
    assert int(raw) == 7


async def test_different_keys_are_independent(fake_redis_client):
    for _ in range(3):
        await rl.check_rate_limit("key:A", limit=3, window_seconds=60)
    with pytest.raises(HTTPException):
        await rl.check_rate_limit("key:A", limit=3, window_seconds=60)

    # key:B has its own counter — should still be under limit
    await rl.check_rate_limit("key:B", limit=3, window_seconds=60)


# ── Cooldown ───────────────────────────────────────────────────────────────────


async def test_cooldown_first_acquire_succeeds(fake_redis_client):
    await rl.check_cooldown("cd:key", cooldown_seconds=60)


async def test_cooldown_second_acquire_raises_429(fake_redis_client):
    await rl.check_cooldown("cd:key", cooldown_seconds=60)
    with pytest.raises(HTTPException) as exc_info:
        await rl.check_cooldown("cd:key", cooldown_seconds=60)
    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "AUTH_OTP_RESEND_COOLDOWN"
    assert "Retry-After" in exc_info.value.headers


async def test_cooldown_retry_after_reflects_remaining_ttl(fake_redis_client):
    await rl.check_cooldown("cd:key", cooldown_seconds=120)
    with pytest.raises(HTTPException) as exc_info:
        await rl.check_cooldown("cd:key", cooldown_seconds=120)
    retry_after = int(exc_info.value.headers["Retry-After"])
    assert 0 < retry_after <= 120


async def test_release_cooldown_allows_immediate_reacquire(fake_redis_client):
    await rl.check_cooldown("cd:key", cooldown_seconds=60)
    await rl.release_cooldown("cd:key")
    # Should succeed — cooldown key is gone
    await rl.check_cooldown("cd:key", cooldown_seconds=60)


async def test_release_cooldown_on_nonexistent_key_is_safe(fake_redis_client):
    # Should not raise even if the key was never set
    await rl.release_cooldown("cd:nonexistent")
