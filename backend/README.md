# TalkTribe Backend

FastAPI backend for the TalkTribe Language Exchange Platform.

## Tech Stack

| Tool | Purpose |
|---|---|
| FastAPI | Web framework |
| PostgreSQL + asyncpg | Primary database (async) |
| SQLAlchemy 2.0 | ORM (async) |
| Alembic | Database migrations |
| Redis | Access token blocklist, caching |
| Pydantic v2 | Request/response validation |
| pydantic-settings | Environment config |
| JWT (python-jose) | Access + refresh token auth |
| aiosmtplib | Async email (OTP delivery) |
| uv | Dependency management |
| Ruff | Formatter + linter |
| MyPy | Static type checking |
| Bandit | Security scanning |
| Pytest | Test suite |

## Setup

See the root [README](../README.md) for Docker setup. The backend runs inside the `talktribe_backend` container.

## Environment Variables

Copy `.env.example` to `.env` and fill in values:

```bash
cp .env.example .env
```

Key variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (uses `postgres:5432` inside Docker) |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT access token signing key (min 32 chars) |
| `REFRESH_SECRET_KEY` | JWT refresh token signing key (min 32 chars) |
| `SMTP_*` | Email credentials for OTP delivery |

> `backend/.env` is for the Python app. The root `.env` is for Docker Compose. They are separate by design.

## Running Checks Locally

All commands run from `backend/`:

```bash
cd backend

uv run ruff format --check .                                          # format check
uv run ruff check .                                                   # lint
DATABASE_URL=sqlite+aiosqlite:///./test_ci.db uv run pytest -v       # tests
uv run mypy app                                                       # type check
uv run bandit -r app -c pyproject.toml                                # security scan
```

Migrations (Docker must be running):

```bash
docker-compose exec backend uv run alembic upgrade head   # apply migrations
docker-compose exec backend uv run alembic check          # detect schema drift
```

## Project Structure

```
app/
├── main.py                          # FastAPI app, lifespan, middleware
├── api/
│   └── v1/router.py                 # Mounts all domain routers
├── domains/
│   └── auth/                        # Auth domain
│       ├── api/routes.py            # HTTP endpoints
│       ├── application/             # auth_service.py, otp_service.py
│       ├── domain/otp_utils.py      # OTP generation (pure logic)
│       ├── infrastructure/          # DB models, repository
│       └── schemas/                 # Pydantic schemas
└── infrastructure/
    ├── config/config.py             # Settings loaded from backend/.env
    ├── database/                    # Async SQLAlchemy engine + session
    ├── cache/redis.py               # Redis client
    ├── email/email_service.py       # Async SMTP
    └── security/                    # jwt.py, password.py
```

## Auth Flow

```
POST /api/v1/auth/register     → create user, send OTP email
POST /api/v1/auth/verify-otp   → verify OTP, activate account
POST /api/v1/auth/login        → returns access + refresh tokens
POST /api/v1/auth/refresh      → rotate tokens, blocklist old access token
POST /api/v1/auth/logout       → blocklist access token in Redis
```

Access tokens expire in 15 minutes. Refresh tokens expire in 7 days. Logged-out or rotated access tokens are added to a Redis blocklist and rejected on every request.
