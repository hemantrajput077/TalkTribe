# TalkTribe — Language Exchange Platform

A real-time language exchange platform built with FastAPI, React, PostgreSQL, Redis, and WebRTC.

## Quick Start

### Prerequisites

- Docker Desktop installed and running
- Git

### Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd TalkTribe

# 2. Create environment files
cp .env.example .env
cp backend/.env.example backend/.env   # edit values if needed

# 3. Start all services
docker-compose up --build
```

### Access Points

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:**5433** |
| Redis | localhost:6379 |

> PostgreSQL is mapped to port **5433** on your machine (not 5432) to avoid conflicts with any local Postgres installation.

---

## Project Structure

```
TalkTribe/
├── backend/
│   ├── app/
│   │   ├── main.py                         # FastAPI app entry point
│   │   ├── api/v1/router.py                # Top-level API router
│   │   ├── domains/
│   │   │   └── auth/                       # Auth domain (DDD)
│   │   │       ├── api/routes.py           # Auth HTTP endpoints
│   │   │       ├── application/            # Business logic (services)
│   │   │       ├── domain/                 # Pure domain logic (OTP utils)
│   │   │       ├── infrastructure/         # DB models, repository
│   │   │       └── schemas/                # Pydantic request/response models
│   │   └── infrastructure/
│   │       ├── config/config.py            # Settings (pydantic-settings)
│   │       ├── database/                   # SQLAlchemy async session
│   │       ├── cache/redis.py              # Redis client
│   │       ├── email/email_service.py      # SMTP email
│   │       └── security/                   # JWT + password hashing
│   ├── alembic/                            # Database migrations
│   ├── tests/                              # Pytest test suite
│   ├── backend/.env                        # Backend environment variables
│   └── pyproject.toml                      # Dependencies + tool config
├── frontend/
│   ├── src/
│   │   ├── App.tsx                         # Root React component
│   │   └── main.tsx                        # React entry point
│   └── Dockerfile.dev
├── .env                                    # Docker Compose variables
└── docker-compose.yml
```

---

## Development Commands

### Docker

```bash
docker-compose up           # Start all services
docker-compose up -d        # Start in background
docker-compose up --build   # Rebuild images and start
docker-compose down         # Stop all services
docker-compose down -v      # Stop and delete volumes (wipes DB)
docker-compose logs -f      # Stream all logs
docker-compose logs -f backend   # Stream backend logs only
```

### Backend — run from `backend/`

```bash
cd backend

# Format code
uv run ruff format .

# Lint
uv run ruff check --fix .

# Type check
uv run mypy app

# Tests (uses SQLite, no Docker needed)
DATABASE_URL=sqlite+aiosqlite:///./test_ci.db uv run pytest -v

# Security scan
uv run bandit -r app -c pyproject.toml

# Migrations (Docker must be running)
docker-compose exec backend uv run alembic upgrade head
docker-compose exec backend uv run alembic check
```

### Generate a new migration after changing a model

```bash
docker-compose exec backend uv run alembic revision --autogenerate -m "describe change"
docker-compose exec backend uv run alembic upgrade head
```

---

## Pre-Push Checklist

Run all checks from `backend/` before pushing or opening a PR:

```bash
# Git Bash
cd backend && \
  uv run ruff format --check . && \
  uv run ruff check . && \
  DATABASE_URL=sqlite+aiosqlite:///./test_ci.db uv run pytest -v && \
  uv run mypy app && \
  uv run bandit -r app -c pyproject.toml && \
  echo "All checks passed — safe to push"
```

```powershell
# PowerShell
cd backend
uv run ruff format --check .
uv run ruff check .
$env:DATABASE_URL="sqlite+aiosqlite:///./test_ci.db"; uv run pytest -v
uv run mypy app
uv run bandit -r app -c pyproject.toml
```

| Check | What it verifies |
|---|---|
| `ruff format --check` | Code style (indentation, quotes, spacing) |
| `ruff check` | Code quality (unused imports, bad patterns) |
| `pytest` | Test correctness |
| `mypy` | Type safety |
| `bandit` | Security (hardcoded secrets, injection risks) |
| `alembic check` | No model changes missing a migration |

---

## Current Status

| Feature | Status |
|---|---|
| Docker environment | Done |
| PostgreSQL + Redis | Done |
| FastAPI app structure (DDD) | Done |
| User registration + login | Done |
| JWT access + refresh tokens | Done |
| Email OTP verification | Done |
| Redis access token blocklist | Done |
| WebSocket / real-time chat | Planned |
| WebRTC voice/video | Planned |

---

## Troubleshooting

**Port already in use**
```bash
netstat -ano | findstr :8000
netstat -ano | findstr :5433
# Kill the listed PID or change the port in docker-compose.yml
```

**Clean Docker restart**
```bash
docker-compose down -v
docker-compose up --build
```

**Cannot connect to API**
1. Check logs: `docker-compose logs backend`
2. Verify health: http://localhost:8000/health
3. Check CORS origins in `backend/app/infrastructure/config/config.py`

**`DATABASE_URL` missing error when running pytest**
Always run pytest from inside `backend/`, or pass the URL explicitly:
```bash
DATABASE_URL=sqlite+aiosqlite:///./test_ci.db uv run pytest -v
```

---

## Documentation

See the `docs/` folder for architecture, database design, API design, and learning notes.
