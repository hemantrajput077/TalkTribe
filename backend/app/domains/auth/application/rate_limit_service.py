"""
Auth-domain rate-limit service.

Owns the Redis key namespaces for all auth rate limits and maps each
protected action to the appropriate check_rate_limit / check_cooldown call.
All user-supplied identifiers (IP, email, username) are normalised here so
that routes stay clean and key collisions cannot occur due to case differences.
"""

from __future__ import annotations

from app.infrastructure.cache.rate_limiter import check_cooldown, check_rate_limit, release_cooldown
from app.infrastructure.config.config import settings

# ── Redis key templates ────────────────────────────────────────────────────────

_REGISTER_IP = "rate_limit:auth:register:ip:{ip}"
_LOGIN_IP = "rate_limit:auth:login:ip:{ip}"
_LOGIN_USER = "rate_limit:auth:login:username:{username}"
_VERIFY_EMAIL = "rate_limit:auth:verify_email:email:{email}"
_RESEND_OTP = "rate_limit:auth:resend_otp:email:{email}"
_RESEND_COOLDOWN = "rate_limit:auth:resend_otp:cooldown:email:{email}"


# ── Public API ─────────────────────────────────────────────────────────────────


async def check_register_rate_limit(ip: str) -> None:
    await check_rate_limit(
        key=_REGISTER_IP.format(ip=ip),
        limit=settings.RATE_LIMIT_REGISTER_IP_MAX,
        window_seconds=settings.RATE_LIMIT_REGISTER_WINDOW_SECONDS,
    )


async def check_login_rate_limit(ip: str, username: str) -> None:
    """Check both the per-IP and per-username login limits."""
    normalized = username.strip().lower()
    await check_rate_limit(
        key=_LOGIN_IP.format(ip=ip),
        limit=settings.RATE_LIMIT_LOGIN_IP_MAX,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    )
    await check_rate_limit(
        key=_LOGIN_USER.format(username=normalized),
        limit=settings.RATE_LIMIT_LOGIN_USERNAME_MAX,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    )


async def check_verify_email_rate_limit(email: str) -> None:
    normalized = email.strip().lower()
    await check_rate_limit(
        key=_VERIFY_EMAIL.format(email=normalized),
        limit=settings.RATE_LIMIT_VERIFY_EMAIL_MAX,
        window_seconds=settings.RATE_LIMIT_VERIFY_EMAIL_WINDOW_SECONDS,
    )


async def check_resend_otp_rate_limit(email: str) -> None:
    normalized = email.strip().lower()
    await check_rate_limit(
        key=_RESEND_OTP.format(email=normalized),
        limit=settings.RATE_LIMIT_RESEND_OTP_MAX,
        window_seconds=settings.RATE_LIMIT_RESEND_OTP_WINDOW_SECONDS,
    )


async def acquire_resend_otp_cooldown(email: str) -> None:
    normalized = email.strip().lower()
    await check_cooldown(
        key=_RESEND_COOLDOWN.format(email=normalized),
        cooldown_seconds=settings.RATE_LIMIT_RESEND_OTP_COOLDOWN_SECONDS,
    )


async def release_resend_otp_cooldown(email: str) -> None:
    normalized = email.strip().lower()
    await release_cooldown(key=_RESEND_COOLDOWN.format(email=normalized))
