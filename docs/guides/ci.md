# TalkTribe — CI (Continuous Integration) Documentation

## Overview

**CI (Continuous Integration)** is an automated system that runs a series of checks on a fresh Linux machine every time you push code or raise a Pull Request on GitHub.

Its purpose is to:
- ✅ Prevent bad code from being merged
- ✅ Automatically check formatting, code quality, types, and security
- ✅ Verify database migrations are valid and up to date
- ✅ Confirm all tests pass before merging

---

## CI File Location

```
TalkTribe/
└── .github/
    └── workflows/
        └── ci.yml          ← Single file — the entire CI pipeline is defined here
```

---

## When CI Triggers

```yaml
on:
  push:
    branches:
      - "**"         # Any branch push → CI runs
  pull_request:
    branches:
      - "**"         # Any PR raised → CI runs
```

| Action | CI Runs? |
|---|---|
| Push to `main` | ✅ |
| Push to `develop` | ✅ |
| Push to `feature/xyz` | ✅ |
| Any PR raised | ✅ |
| PR merged | ✅ (merge = push) |

---

## CI Machine & Environment

- **OS:** `ubuntu-latest` (fresh Linux VM — new machine on every run)
- **Working Directory:** `backend/` (all commands run from here)
- **Service Started:** PostgreSQL 16 (only used for the Alembic step)

### Environment Variables (fake CI-only secrets)

| Variable | CI Value |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://talktribe:ci_password@localhost:5432/talktribe_ci` |
| `SECRET_KEY` | `ci-test-secret-key-at-least-32-chars-long!!!` |
| `REFRESH_SECRET_KEY` | `ci-test-refresh-key-at-least-32-chars-long!!` |
| `JWT_SECRET_KEY` | `ci-test-jwt-key-at-least-32-chars-long!!!!!!` |

> ⚠️ These are **not real secrets** — they are placeholder values used only during CI.
> Real secrets live in the `.env` file which is excluded via `.gitignore`.

---

## GitHub Actions Used (3 total)

| Action | Version | Purpose |
|---|---|---|
| `actions/checkout` | v4 | Downloads the repo code onto the CI machine |
| `actions/setup-python` | v5 | Installs Python 3.11 |
| `astral-sh/setup-uv` | v4 | Installs the `uv` package manager |

---

## Packages Installed (Step 4: `uv sync --all-groups`)

### Production Dependencies (12 packages)

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn[standard]` | ASGI server |
| `sqlalchemy` | ORM / database layer |
| `alembic` | Database migrations |
| `asyncpg` | PostgreSQL async driver |
| `pydantic` | Data validation |
| `pydantic-settings` | Load config from `.env` |
| `python-jose[cryptography]` | JWT tokens |
| `passlib[bcrypt]` + `pwdlib` | Password hashing |
| `aiosmtplib` | Async email sending (OTP) |
| `redis` | Cache / sessions |
| `python-dotenv` | Load `.env` file |
| `python-multipart` | Form data parsing |

### Dev / CI Dependencies (7 packages)

| Package | Purpose | CI Step |
|---|---|---|
| `ruff` | Code formatter + linter | Steps 5, 6 |
| `mypy` | Static type checker | Step 8 |
| `bandit` | Security vulnerability scanner | Step 9 |
| `pytest` | Test runner | Step 7 |
| `pytest-asyncio` | Async test support | Step 7 |
| `httpx` | HTTP client for testing | Step 7 |
| `aiosqlite` | SQLite async driver (tests use SQLite) | Step 7 |

---

## 10 Steps — Detailed Breakdown

### Step 1 — Checkout Repository

```yaml
- name: Checkout repository
  uses: actions/checkout@v4
```

- **Action:** `actions/checkout@v4`
- **Purpose:** Downloads the entire repository code onto the CI machine
- **Files used:** Entire repository
- **Packages:** None

---

### Step 2 — Set up Python

```yaml
- name: Set up Python 3.11
  uses: actions/setup-python@v5
  with:
    python-version: "3.11"
```

- **Action:** `actions/setup-python@v5`
- **Purpose:** Installs Python 3.11 on the CI machine
- **Files used:** None

---

### Step 3 — Set up uv

```yaml
- name: Set up uv
  uses: astral-sh/setup-uv@v4
  with:
    version: "latest"
```

- **Action:** `astral-sh/setup-uv@v4`
- **Purpose:** Installs the `uv` package manager (10–100x faster than pip)
- **Files used:** None

---

### Step 4 — Install Dependencies

```yaml
- name: Install dependencies
  run: uv sync --all-groups
```

- **Purpose:** Installs all 19 production + dev packages
- **Files read:** `pyproject.toml`, `uv.lock`
- **Output:** Creates the `.venv/` virtual environment folder

---

### Step 5 — Ruff Format Check

```yaml
- name: Ruff format check
  run: uv run ruff format --check .
```

- **Package:** `ruff`
- **Purpose:** Verifies all code is properly formatted — correct quotes, indentation, blank lines
- **Does NOT auto-fix** — only checks and fails if formatting is wrong
- **Files checked:** All `.py` files in `backend/`
- **Config in `pyproject.toml`:**

```toml
[tool.ruff.format]
quote-style = "double"    # double quotes required
indent-style = "space"    # spaces, not tabs
```

---

### Step 6 — Ruff Lint

```yaml
- name: Ruff lint
  run: uv run ruff check .
```

- **Package:** `ruff`
- **Purpose:** Checks for code quality issues
- **Config in `pyproject.toml`:**

```toml
[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B"]
```

| Rule Set | What It Catches |
|---|---|
| `E` | PEP8 style errors |
| `F` | Undefined names, unused imports |
| `W` | Warnings |
| `I` | Import ordering (isort) |
| `UP` | Outdated Python syntax |
| `B` | Common bugs (flake8-bugbear) |

---

### Step 7 — Pytest

```yaml
- name: Pytest
  run: uv run pytest -v
  env:
    DATABASE_URL: sqlite+aiosqlite:///./test_ci.db
```

- **Packages:** `pytest`, `pytest-asyncio`, `httpx`, `aiosqlite`
- **Database:** SQLite (PostgreSQL not required for tests)
- **Files used:**

| File | Role |
|---|---|
| `tests/conftest.py` | Sets env vars + creates async HTTP test client |
| `tests/test_app.py` | App-level endpoint tests |
| `tests/test_jwt.py` | JWT token tests |
| `tests/test_schemas.py` | Pydantic schema validation tests |
| `pytest.ini` | `asyncio_mode = auto` setting |

- **Temp file created:** `test_ci.db` (SQLite DB used during test run)

---

### Step 8 — MyPy

```yaml
- name: MyPy
  run: uv run mypy app
```

- **Package:** `mypy`
- **Purpose:** Static type checker — verifies type hints are correct throughout the codebase
- **Files checked:** `backend/app/**/*.py`
- **Config in `pyproject.toml`:**

```toml
[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
exclude = ["alembic/", ".venv/", "tests/"]
```

---

### Step 9 — Bandit Security Scan

```yaml
- name: Bandit security scan
  run: uv run bandit -r app -c pyproject.toml
```

- **Package:** `bandit`
- **Purpose:** Scans for security vulnerabilities:
  - Hardcoded passwords or secrets
  - Use of `eval()` or `exec()`
  - Insecure random (`random` module — this is why `secrets` is used instead)
  - SQL injection risks
  - Weak cryptography
- **Files scanned:** `backend/app/` (recursive)
- **Config in `pyproject.toml`:**

```toml
[tool.bandit]
exclude_dirs = [".venv", "alembic/versions", "tests"]
skips = []
```

---

### Step 10 — Alembic Migrations

```yaml
- name: Alembic — apply migrations
  run: uv run alembic upgrade head

- name: Alembic — check for missing migrations
  run: uv run alembic check
```

- **Packages:** `alembic`, `asyncpg`
- **Database:** PostgreSQL 16 (CI service container)
- **Purpose:**
  1. `upgrade head` — Applies all migration files against the real PostgreSQL DB. Fails if any migration has a SQL error.
  2. `alembic check` — Compares SQLAlchemy models against the DB schema. Fails if a model was changed but no migration was created.
- **Files used:**

| File | Role |
|---|---|
| `alembic.ini` | Alembic configuration |
| `alembic/env.py` | Migration environment setup |
| `alembic/versions/*.py` | Individual migration scripts |
| `app/models/*.py` | SQLAlchemy model definitions |

---

## Files Created for CI (5 new files)

```
.github/workflows/ci.yml       ← CI pipeline definition
backend/tests/conftest.py      ← Pytest config + async HTTP client fixture
backend/tests/test_app.py      ← App-level endpoint tests
backend/tests/test_jwt.py      ← JWT token tests
backend/tests/test_schemas.py  ← Pydantic schema validation tests
```

## Files Modified for CI (2 files)

```
backend/pyproject.toml    ← Added dev dependencies + ruff/mypy/bandit/pytest config sections
backend/pytest.ini        ← Added asyncio_mode = auto
```

## Files Read by CI (not changed)

```
backend/uv.lock               → Exact package versions (Step 4)
backend/alembic.ini           → Alembic settings (Step 10)
backend/alembic/versions/*.py → Migration scripts (Step 10)
backend/app/**/*.py           → Ruff (5,6), MyPy (8), Bandit (9)
backend/app/models/*.py       → Alembic model check (Step 10)
```

---

## Complete Flow Diagram

```
Push code or raise a PR
          │
          ▼
 GitHub spins up a fresh Ubuntu VM
 + starts PostgreSQL 16 service
          │
          ▼
Step 1  → Checkout         (download repo code)
Step 2  → Python 3.11      (install Python)
Step 3  → uv               (install package manager)
Step 4  → uv sync          (install all 19 packages)
          │
          ├──▶ Step 5:  Ruff format  → Wrong formatting?      FAIL ❌
          ├──▶ Step 6:  Ruff lint    → Code quality issues?   FAIL ❌
          ├──▶ Step 7:  Pytest       → Any tests failing?     FAIL ❌
          ├──▶ Step 8:  MyPy         → Type errors?           FAIL ❌
          ├──▶ Step 9:  Bandit       → Security issues?       FAIL ❌
          └──▶ Step 10: Alembic      → Missing migrations?    FAIL ❌
                    │
         ALL PASS ──┴── ANY FAIL
              ✅              ❌
          Merge OK        Merge Blocked
```

---

## Quick Fix Reference

| CI Step Failed | Likely Reason | How to Fix Locally |
|---|---|---|
| Ruff format | Wrong quotes / spacing / indentation | `uv run ruff format .` |
| Ruff lint | Unused imports / bad patterns | `uv run ruff check --fix .` |
| Pytest | A test is failing | Fix the failing test or the code it tests |
| MyPy | Incorrect type annotation | Fix the type hint in the relevant file |
| Bandit | Security vulnerability detected | Remove or replace the dangerous code pattern |
| Alembic upgrade | A migration script has a SQL error | Fix the migration file in `alembic/versions/` |
| Alembic check | Model changed but no migration created | `uv run alembic revision --autogenerate -m "describe change"` |

---

## Summary Table

| # | Step | Action / Library | Files Read | Creates |
|---|---|---|---|---|
| 1 | Checkout | `actions/checkout@v4` | Entire repo | — |
| 2 | Python | `actions/setup-python@v5` | — | Python 3.11 |
| 3 | uv | `astral-sh/setup-uv@v4` | — | uv tool |
| 4 | Install deps | `uv sync` | `pyproject.toml`, `uv.lock` | `.venv/` |
| 5 | Ruff format | `ruff` | All `.py` files | — |
| 6 | Ruff lint | `ruff` | All `.py` files | — |
| 7 | Pytest | `pytest`, `httpx`, `aiosqlite` | `tests/`, `conftest.py` | `test_ci.db` |
| 8 | MyPy | `mypy` | `app/**/*.py` | `.mypy_cache/` |
| 9 | Bandit | `bandit` | `app/**/*.py` | — |
| 10 | Alembic | `alembic`, `asyncpg` | `alembic/`, `app/models/` | — |
