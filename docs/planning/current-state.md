 TalkTribe — Current State Report

  Project Structure

  TalkTribe/
  ├── backend/
  │   ├── app/
  │   │   ├── main.py                     ← FastAPI entry point
  │   │   ├── config.py                   ← Primary settings (pydantic-settings)
  │   │   ├── database.py                 ← Primary async engine + get_db dependency
  │   │   ├── routers.py                  ← Top-level router that includes auth
  │   │   ├── api/v1/auth.py              ← All auth endpoints
  │   │   ├── core/
  │   │   │   ├── config.py               ← SECOND settings class (different field names!)
  │   │   │   ├── jwt.py                  ← JWT creation/verification
  │   │   │   ├── security.py             ← Password hashing (pwdlib)
  │   │   │   └── exceptions.py           ← Custom exception hierarchy
  │   │   ├── db/
  │   │   │   ├── base.py                 ← declarative_base()
  │   │   │   ├── database.py             ← SECOND engine (uses app/core/config.py)
  │   │   │   ├── session.py              ← Re-exports SessionLocal
  │   │   │   └── dependencies.py         ← Re-exports get_db from app.database
  │   │   ├── models/
  │   │   │   ├── auth.py                 ← User model
  │   │   │   ├── otp.py                  ← Otp model
  │   │   │   └── refresh_token.py        ← RefreshToken model
  │   │   ├── schemas/
  │   │   │   ├── auth.py                 ← CreateUser, RegisterResponse, UserLogin
  │   │   │   ├── otp.py                  ← VerifyEmailRequest, ResendOTPRequest, OTPResponse
  │   │   │   └── token.py                ← Token, RefreshRequest, LogoutRequest
  │   │   ├── services/
  │   │   │   ├── auth_service.py         ← AuthService class + get_current_user dependency
  │   │   │   ├── otp_service.py          ← create_otp, verify_otp, expire_old_otps, resend_otp
  │   │   │   └── email_service.py        ← send_otp_email via aiosmtplib
  │   │   ├── repositories/
  │   │   │   └── auth_repository.py      ← AuthRepository (refresh token CRUD)
  │   │   ├── utils/
  │   │   │   ├── otp.py                  ← generate_otp() (cryptographic)
  │   │   │   └── security.py             ← SECOND password hashing (passlib — UNUSED)
  │   │   └── websocket/
  │   │       └── __init__.py             ← EMPTY
  │   ├── alembic/
  │   │   ├── env.py                      ← Async-aware Alembic env
  │   │   └── versions/
  │   │       ├── c36d28f94a42_*.py       ← Migration 1: Create users
  │   │       ├── a7b3c9d2e1f4_*.py       ← Migration 2: Add OTP + is_verified
  │   │       └── 748a3a90d846_.py        ← Migration 3: Add refresh_tokens
  │   └── tests/
  │       ├── __init__.py                 ← EMPTY
  │       └── token.py                    ← Manual script, not a pytest test
  ├── frontend/
  │   └── src/
  │       ├── App.tsx                     ← Static placeholder + API status button
  │       └── config/constants.ts         ← API endpoint constants (defined, unused)
  ├── docker-compose.yml                  ← 4 services: postgres, redis, backend, frontend
  └── docs/
      ├── milestone-1.1-explanation.md
      └── quick-reference.md

  ---
  Item-by-Item Analysis

  ---
  1. Project Structure

  Status: IMPLEMENTED

  Clean layered structure: api → services → repositories → models. Frontend and backend are separate services. Docker
  Compose orchestrates 4 containers. Docs folder exists with two documents.

  Observation: ARCHITECTURE.md and MILESTONES.md describe the planned full-scale system (languages, friendships,
  messages, calls, WebRTC), which is far beyond what is currently built.

  ---
  2. Backend Architecture

  Status: IMPLEMENTED (with duplication issues)

  - Files: app/main.py, app/routers.py, app/api/v1/auth.py
  - FastAPI app is created in main.py, CORS middleware is configured, the router chain is main.py → routers.py →
  api/v1/auth.py
  - All routes carry the prefix /api/v1/auth
  - Swagger UI at /api/docs, ReDoc at /api/redoc
  - GET /health returns hardcoded "database": "connected" and "redis": "connected" — these are not real checks

  Critical Observation — Duplicate Infrastructure:

  ┌──────────┬─────────────────────────────────┬───────────────────────────────────┬───────────────────────────────┐
  │  Layer   │           First Copy            │            Second Copy            │         Which is Used         │
  ├──────────┼─────────────────────────────────┼───────────────────────────────────┼───────────────────────────────┤
  │ Config   │ app/config.py (has              │ app/core/config.py (has           │ Both — JWT uses core/config,  │
  │          │ JWT_SECRET_KEY, OTP_*, SMTP_*)  │ SECRET_KEY, REFRESH_SECRET_KEY)   │ OTP/email use app/config      │
  ├──────────┼─────────────────────────────────┼───────────────────────────────────┼───────────────────────────────┤
  │ Password │ app/utils/security.py (passlib) │ app/core/security.py (pwdlib)     │ Only core/security (pwdlib)   │
  │          │                                 │                                   │ is used by auth_service.py    │
  ├──────────┼─────────────────────────────────┼───────────────────────────────────┼───────────────────────────────┤
  │ Database │ app/database.py (primary engine │ app/db/database.py (second engine │ app/database.py is the one    │
  │          │  from app/config)               │  from app/core/config)            │ injected by get_db            │
  └──────────┴─────────────────────────────────┴───────────────────────────────────┴───────────────────────────────┘

  ---
  3. Frontend Architecture

  Status: PARTIALLY IMPLEMENTED

  - Files: frontend/src/App.tsx, frontend/src/config/constants.ts, frontend/src/main.tsx
  - React 18 + TypeScript + Vite + Tailwind CSS scaffold is complete
  - App.tsx is a static placeholder — one button that calls GET /health and displays the result
  - constants.ts defines API_ENDPOINTS (LOGIN, REGISTER, REFRESH, LOGOUT, etc.) but nothing in the frontend uses them
  - No pages, no routing, no auth forms, no API integration
  - Dependencies installed: react-router-dom, @tanstack/react-query, zustand, axios — none are wired up

  ---
  4. Database Configuration

  Status: IMPLEMENTED (with dual-engine issue)

  - Files: app/database.py, app/db/database.py, app/db/base.py
  - PostgreSQL via asyncpg driver, async SQLAlchemy 2.0
  - app/database.py creates the engine from app/config.settings.DATABASE_URL, pool_size=10, max_overflow=20
  - app/db/database.py creates a second independent engine from app/core/config.settings.DATABASE_URL
  - Both read DATABASE_URL from .env, so in practice they point to the same DB, but they are separate connection pools
  - app/db/base.py declares Base = declarative_base() — this single Base is shared by all models and Alembic
  - docker-compose.yml maps host port 5433 → container port 5432 (non-standard; localhost:5433 connects to the DB)

  ---
  5. Existing Database Models

  Status: IMPLEMENTED

  app/models/auth.py — User:
  - id (Integer PK, indexed), username (String 30, unique, indexed), email (String 255, unique, indexed)
  - password (String 255), full_name (String 100, nullable)
  - is_active (Boolean, default True), is_verified (Boolean, default False)
  - created_at, updated_at (DateTime, server default func.now())
  - Relationship: refresh_tokens → cascade all/delete-orphan

  app/models/otp.py — Otp:
  - id (Integer PK), user_id (FK → users.id), otp (String 6)
  - purpose (String 30), expires_at (DateTime), is_used (Boolean, default False)
  - created_at (DateTime, server_default)

  app/models/refresh_token.py — RefreshToken:
  - id (Integer PK), token (String 500, unique, indexed), user_id (FK → users.id, CASCADE)
  - expires_at (DateTime with timezone), is_revoked (Boolean, default False)
  - created_at (DateTime with timezone, default datetime.utcnow)

  Observation: No models exist yet for languages, user_languages, friendships, messages, or calls (those are only in
  ARCHITECTURE.md as a plan).

  ---
  6. Existing Alembic Migrations

  Status: IMPLEMENTED

  Three migrations exist, in order:

  ┌──────────────┬────────────┬──────────────────────────────────────────────────────────────────────────────────────┐
  │   Revision   │    Date    │                                     What it does                                     │
  ├──────────────┼────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ c36d28f94a42 │ 2026-07-27 │ Creates users table (no is_verified yet)                                             │
  ├──────────────┼────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ a7b3c9d2e1f4 │ 2026-08-03 │ Adds is_verified to users; creates otps table with composite index on (user_id,      │
  │              │            │ purpose)                                                                             │
  ├──────────────┼────────────┼──────────────────────────────────────────────────────────────────────────────────────┤
  │ 748a3a90d846 │ 2026-08-14 │ Creates refresh_tokens table; removes old OTP indexes; shrinks username varchar from │
  │              │            │  50→30; drops timezone from created_at/updated_at                                    │
  └──────────────┴────────────┴──────────────────────────────────────────────────────────────────────────────────────┘

  Migration chain is complete and linear: None → c36d → a7b3 → 748a.

  Observation: Migration 748a3a90d846 removes the ondelete='CASCADE' from otps.user_id FK (drops and recreates without
  it), which diverges slightly from the original migration's intent.

  ---
  7. API Routes/Endpoints

  Status: IMPLEMENTED

  All routes are under /api/v1/auth:

  ┌────────┬────────────────────┬────────────────────┬────────────────────────────────────┐
  │ Method │        Path        │   Auth Required    │            What it does            │
  ├────────┼────────────────────┼────────────────────┼────────────────────────────────────┤
  │ POST   │ /auth/register     │ No                 │ Create user + send OTP             │
  ├────────┼────────────────────┼────────────────────┼────────────────────────────────────┤
  │ POST   │ /auth/verify-email │ No                 │ Verify OTP → activate account      │
  ├────────┼────────────────────┼────────────────────┼────────────────────────────────────┤
  │ POST   │ /auth/resend-otp   │ No                 │ Invalidate old OTPs + send new one │
  ├────────┼────────────────────┼────────────────────┼────────────────────────────────────┤
  │ POST   │ /auth/login        │ No                 │ Authenticate → return token pair   │
  ├────────┼────────────────────┼────────────────────┼────────────────────────────────────┤
  │ POST   │ /auth/refresh      │ No (token in body) │ Rotate refresh token               │
  ├────────┼────────────────────┼────────────────────┼────────────────────────────────────┤
  │ POST   │ /auth/logout       │ No (token in body) │ Revoke single refresh token        │
  ├────────┼────────────────────┼────────────────────┼────────────────────────────────────┤
  │ POST   │ /auth/logout-all   │ Yes (Bearer)       │ Revoke all tokens for user         │
  ├────────┼────────────────────┼────────────────────┼────────────────────────────────────┤
  │ GET    │ /auth/me           │ Yes (Bearer)       │ Return current user's profile      │
  ├────────┼────────────────────┼────────────────────┼────────────────────────────────────┤
  │ GET    │ /auth/user_data    │ No — OPEN          │ Return all users                   │
  ├────────┼────────────────────┼────────────────────┼────────────────────────────────────┤
  │ DELETE │ /auth/users/{id}   │ No — OPEN          │ Delete any user by ID              │
  └────────┴────────────────────┴────────────────────┴────────────────────────────────────┘

  ---
  8. Authentication — Complete Request Flow Trace

  Registration (POST /api/v1/auth/register):
  Request body (JSON) → Pydantic CreateUser validates:
    - username: 3-30 chars, alphanumeric+underscore, not reserved ("admin","root", etc.)
    - email: normalized to lowercase
    - password: ≥8 chars, must have uppercase, lowercase, digit, special char
    - full_name: optional, alpha only, title-cased

  → AuthService.check_username_exist() → SELECT * FROM users WHERE username=? → 400 if found
  → AuthService.check_email_exist()    → SELECT * FROM users WHERE email=?    → 400 if found

  → AuthService.create_user():
      hash_password(password)   ← pwdlib BcryptHasher
      User(username, email, password_hash, full_name)  ← is_verified=False (default)
      db.add(user) → db.commit() → db.refresh(user)

  → create_otp(db, user.id, purpose="REGISTER"):
      generate_otp(6)           ← secrets.randbelow(10) × 6  [CSPRNG]
      expires_at = utcnow() + 5 min
      Otp(user_id, otp=plain_code, purpose, expires_at, is_used=False)
      db.add(otp) → db.commit()
      returns plain OTP string

  → send_otp_email(email, otp_code, username):
      aiosmtplib.send() → STARTTLS → SMTP_HOST:587
      HTML email with styled OTP display
      returns True/False

  → if email fails: raise HTTP 500
  → if success: return OTPResponse(message="Registration successful! OTP sent to ...")

  OTP Verification (POST /api/v1/auth/verify-email):
  Request: {email, otp}
  → verify_otp(db, email, otp, purpose="REGISTER"):
      SELECT user WHERE email=?  → 404 if not found
      SELECT otp WHERE user_id=? AND purpose=? AND is_used=False AND expires_at > utcnow()
        ORDER BY created_at DESC  → 400 if none found
      compare otp_record.otp == provided_otp  → 400 "Invalid OTP" if mismatch
      otp_record.is_used = True
      user.is_verified = True
      db.commit()
  → Return OTPResponse("Email verified successfully! You can now login.")

  Login (POST /api/v1/auth/login):
  Request: {username, password}
  → AuthService.login() → authenticate_user():
      SELECT user WHERE username=?
      if user is None: uses dummy_hash for constant-time comparison
      verify_password(plain, stored_hash)  ← pwdlib verify
      if mismatch or no user: HTTP 401 "Incorrect username or password."
      if not is_active: HTTP 403 "Account is disabled."
      if not is_verified: HTTP 403 "Email not verified..."

  → _issue_tokens(user):
      create_access_token(user.id, user.email):
          payload = {sub: str(id), email, type:"access", jti:uuid4(), iat, exp: +15min}
          jwt.encode(payload, SECRET_KEY, HS256)

      create_refresh_token(user.id, user.email):
          payload = {sub: str(id), email, type:"refresh", jti:uuid4(), iat, exp: +7days}
          jwt.encode(payload, REFRESH_SECRET_KEY, HS256)   ← different key!
          returns (token_string, expires_at)

      AuthRepository.save_refresh_token(user.id, token, expires_at):
          RefreshToken(user_id, token, expires_at, is_revoked=False)
          db.add() → db.commit()

  → Return Token(access_token, refresh_token, token_type="Bearer")

  Protected Endpoint (GET /api/v1/auth/me):
  Authorization: Bearer <access_token>
  → get_current_user dependency:
      HTTPBearer extracts credentials.credentials
      verify_access_token(token):
          jwt.decode(token, SECRET_KEY, HS256)
          if expired: HTTP 401 "Token has expired."
          if invalid: HTTP 401 "Could not validate credentials."
          if payload["type"] != "access": HTTP 401
      extract user_id from payload["sub"]
      SELECT user WHERE id=user_id → 401 if not found
      if not is_active: HTTP 403
  → Return RegisterResponse (id, username, full_name, email, is_active, is_verified, created_at)

  Token Refresh (POST /api/v1/auth/refresh):
  Request: {refresh_token}
  → verify_refresh_token(token) → validates against REFRESH_SECRET_KEY, enforces type="refresh"
  → AuthRepository.get_valid_token(token):
      SELECT WHERE token=? AND is_revoked=False AND expires_at > utcnow()
      → 401 if not found (already revoked or expired)
  → AuthService.get_user_by_id(payload["sub"]) → 401 if gone or inactive
  → AuthRepository.revoke_token(old_token)  ← is_revoked = True
  → _issue_tokens(user)  ← issues fresh pair, saves new refresh token to DB

  ---
  9. JWT Implementation

  Status: IMPLEMENTED

  - File: app/core/jwt.py
  - Library: python-jose
  - Two separate signing secrets: SECRET_KEY (access) and REFRESH_SECRET_KEY (refresh) from app/core/config.py
  - Token payload: sub, email, type, jti (UUID4), iat, exp
  - Type enforcement: verify_access_token explicitly checks payload["type"] == "access", preventing a refresh token from
  being used as an access token
  - get_token_jti() can extract jti even from expired tokens (for revocation)

  Critical Observation: app/core/config.py has SECRET_KEY = secrets.token_urlsafe(64) as default. The docker-compose.yml
  sets JWT_SECRET_KEY in the environment — but app/core/config.py reads SECRET_KEY, not JWT_SECRET_KEY. This means in
  the Docker environment, SECRET_KEY uses its auto-generated random default, causing all tokens to be invalidated on
  every container restart.

  ---
  10. Authorization / Protected Routes

  Status: PARTIALLY IMPLEMENTED

  - GET /auth/me is protected via get_current_user dependency
  - POST /auth/logout-all is protected via get_current_user
  - GET /auth/user_data — completely open, returns all user records
  - DELETE /auth/users/{user_id} — completely open, no authorization at all
  - No role-based access control
  - No admin middleware

  ---
  11. Repository Layer

  Status: IMPLEMENTED

  - File: app/repositories/auth_repository.py
  - AuthRepository class, injected into AuthService
  - Methods: save_refresh_token, revoke_token, revoke_all_user_tokens, delete_expired_tokens, get_valid_token
  - Note: app/repositories/__init__.py does not exist (no __init__.py in the repositories directory)

  ---
  12. Service Layer

  Status: IMPLEMENTED

  - app/services/auth_service.py: AuthService class — user CRUD, authentication, token lifecycle, get_current_user
  dependency function
  - app/services/otp_service.py: Standalone async functions — create_otp, verify_otp, expire_old_otps, resend_otp
  - app/services/email_service.py: send_otp_email via aiosmtplib, styled HTML emails

  ---
  13. Schema/Pydantic Layer

  Status: IMPLEMENTED

  - app/schemas/auth.py:
    - CreateUser: strict username validation (regex, reserved words), email normalization, 4-rule password validator
    - RegisterResponse: response shape with from_attributes=True
    - UserLogin: username + password
  - app/schemas/otp.py: VerifyEmailRequest (pattern ^\d{6}$), ResendOTPRequest, OTPResponse
  - app/schemas/token.py: Token, RefreshRequest, LogoutRequest, TokenPayload

  ---
  14. WebSocket Implementation

  Status: NOT IMPLEMENTED

  - File: app/websocket/__init__.py is empty
  - No WebSocket endpoints, no connection manager, no handlers, no signaling

  ---
  15. Redis Usage

  Status: NOT IMPLEMENTED

  - redis>=8.0.1 is in pyproject.toml
  - docker-compose.yml provisions a Redis container and passes REDIS_URL to backend
  - app/config.py has REDIS_URL: str = "redis://localhost:6379/0"
  - Zero Redis client code exists in the application. No connection setup, no usage anywhere.

  ---
  16. Testing

  Status: NOT IMPLEMENTED

  - backend/tests/__init__.py — empty file
  - backend/tests/token.py — a manual script (not a pytest test) that manually calls JWT functions and prints output.
  Contains a comment about circular imports. Not runnable as pytest.
  - backend/pytest.ini — empty file, no pytest configuration
  - backend/test_db_connection.py — a manual async script that connects to the DB and lists tables. Not a pytest test.
  - No test fixtures, no test database setup, no conftest.py, no actual test functions

  ---
  17. Configuration / Environment Management

  Status: PARTIALLY IMPLEMENTED

  Two separate Settings classes create confusion:

  ┌─────────────────┬────────────────────────────────────────────────────────┬────────────────────────────────┐
  │     Setting     │                     app/config.py                      │       app/core/config.py       │
  ├─────────────────┼────────────────────────────────────────────────────────┼────────────────────────────────┤
  │ DB URL          │ DATABASE_URL                                           │ DATABASE_URL                   │
  ├─────────────────┼────────────────────────────────────────────────────────┼────────────────────────────────┤
  │ JWT signing key │ JWT_SECRET_KEY                                         │ SECRET_KEY, REFRESH_SECRET_KEY │
  ├─────────────────┼────────────────────────────────────────────────────────┼────────────────────────────────┤
  │ JWT algorithm   │ JWT_ALGORITHM                                          │ ALGORITHM                      │
  ├─────────────────┼────────────────────────────────────────────────────────┼────────────────────────────────┤
  │ Token expiry    │ ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS │ Same names                     │
  ├─────────────────┼────────────────────────────────────────────────────────┼────────────────────────────────┤
  │ OTP config      │ OTP_LENGTH, OTP_EXPIRE_MINUTES                         │ Not present                    │
  ├─────────────────┼────────────────────────────────────────────────────────┼────────────────────────────────┤
  │ SMTP config     │ All SMTP_* fields                                      │ Not present                    │
  ├─────────────────┼────────────────────────────────────────────────────────┼────────────────────────────────┤
  │ Redis           │ REDIS_URL                                              │ Not present                    │
  ├─────────────────┼────────────────────────────────────────────────────────┼────────────────────────────────┤
  │ CORS            │ BACKEND_CORS_ORIGINS                                   │ Not present                    │
  └─────────────────┴────────────────────────────────────────────────────────┴────────────────────────────────┘

  docker-compose.yml sets JWT_SECRET_KEY, JWT_ALGORITHM — these match app/config.py but not app/core/config.py. The JWT
  code uses app/core/config.py, so the Docker env vars have no effect on JWT signing.

  ---
  18. Docker / Containerization

  Status: IMPLEMENTED

  - docker-compose.yml: 4 services — postgres:15-alpine, redis:7-alpine, backend (FastAPI), frontend (React/Vite)
  - Health checks on postgres and redis; backend depends on both being healthy
  - Postgres exposed on 5433:5432 (host:container)
  - Redis exposed on 6379:6379
  - Backend Dockerfile (production): installs deps via pip install -e ., runs alembic upgrade head && uvicorn
  - Backend Dockerfile.dev (development): same but --reload flag
  - Frontend Dockerfile.dev: same as production dockerfile (no distinction)
  - .dockerignore exists at root

  ---
  19. CI/CD

  Status: NOT IMPLEMENTED

  No .github/workflows/, no CI pipeline, no deployment scripts.

  ---
  20. API Documentation

  Status: IMPLEMENTED

  - Swagger UI at /api/docs
  - ReDoc at /api/redoc
  - OpenAPI JSON at /api/openapi.json
  - All endpoints have summary= strings and response models defined

  ---
  21. Existing Documentation

  Status: PARTIALLY IMPLEMENTED

  - ARCHITECTURE.md: Describes the full planned architecture (far beyond current state) — useful as a vision document
  - MILESTONES.md: Milestone plans and code templates — describes planned future work
  - docs/milestone-1.1-explanation.md: Detailed explanation of infrastructure setup
  - docs/quick-reference.md: Docker/CLI command reference
  - CLAUDE.md: Project instructions for this AI coding session
  - Missing: api-design.md, database-design.md, learning-notes.md, decisions.md (all referenced in CLAUDE.md but not
  created)

  ---
  Summary Tables

  A. Implemented Features

  ┌───────────────────────────────────────────┬───────────────────────────────────────────────────────────────────┐
  │                  Feature                  │                             Key Files                             │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ FastAPI application scaffold              │ app/main.py, app/routers.py                                       │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ CORS middleware                           │ app/main.py, app/config.py                                        │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ User registration endpoint                │ app/api/v1/auth.py, app/services/auth_service.py                  │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ OTP generation (CSPRNG)                   │ app/utils/otp.py, app/services/otp_service.py                     │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ OTP storage in DB                         │ app/models/otp.py, app/services/otp_service.py                    │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ OTP verification + account activation     │ app/services/otp_service.py                                       │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ OTP resend (invalidates old OTPs)         │ app/services/otp_service.py                                       │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Email delivery (SMTP/STARTTLS)            │ app/services/email_service.py                                     │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Password hashing (bcrypt via pwdlib)      │ app/core/security.py                                              │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Strong password validation                │ app/schemas/auth.py                                               │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Login with is_verified check              │ app/services/auth_service.py                                      │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ JWT access tokens (15 min)                │ app/core/jwt.py                                                   │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ JWT refresh tokens (7 days, separate key) │ app/core/jwt.py                                                   │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Refresh token DB persistence              │ app/models/refresh_token.py, app/repositories/auth_repository.py  │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Token rotation on refresh                 │ app/services/auth_service.py                                      │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Single-device logout                      │ app/services/auth_service.py, app/repositories/auth_repository.py │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ All-device logout                         │ app/services/auth_service.py, app/repositories/auth_repository.py │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Protected route (/auth/me)                │ app/api/v1/auth.py, app/services/auth_service.py                  │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Async SQLAlchemy 2.0 + asyncpg            │ app/database.py                                                   │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Database models (User, Otp, RefreshToken) │ app/models/                                                       │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Alembic migrations (3 applied)            │ alembic/versions/                                                 │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Repository pattern                        │ app/repositories/auth_repository.py                               │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Service layer                             │ app/services/                                                     │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Pydantic schema layer                     │ app/schemas/                                                      │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Docker Compose (4 services)               │ docker-compose.yml                                                │
  ├───────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Swagger/ReDoc documentation               │ app/main.py                                                       │
  └───────────────────────────────────────────┴───────────────────────────────────────────────────────────────────┘

  B. Partially Implemented Features

  ┌─────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────┐
  │         Feature         │                                          Gap                                          │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
  │ Configuration           │ Two separate Settings classes with overlapping but incompatible field names; Docker   │
  │ management              │ env vars don't reach JWT module                                                       │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
  │ Password hashing        │ Two implementations exist (utils/security.py passlib, core/security.py pwdlib); only  │
  │                         │ pwdlib is actually used                                                               │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
  │ Database setup          │ Two separate engine instances; app/db/database.py is a second independent engine      │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
  │ Frontend                │ Scaffold only; no auth forms, no routing, no pages                                    │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
  │ Health check endpoint   │ Returns hardcoded "connected" — does not actually verify DB or Redis connectivity     │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────┤
  │ Refresh token expiry    │ delete_expired_tokens() method exists in repository but is never called (no           │
  │ cleanup                 │ scheduler)                                                                            │
  └─────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────┘

  C. Not Implemented Features

  ┌──────────────────────────┬─────────────────────────────────────────────────────────────────────┐
  │         Feature          │                               Status                                │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ Test suite               │ No tests; pytest.ini is empty                                       │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ Redis integration        │ Installed and containerized, but zero code usage                    │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ WebSocket                │ app/websocket/__init__.py is empty                                  │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ User profile management  │ No update endpoint                                                  │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ Language/matching system │ Not started                                                         │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ Friendship system        │ Not started                                                         │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ Real-time messaging      │ Not started                                                         │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ WebRTC/voice calling     │ Not started                                                         │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ Password reset flow      │ Not started                                                         │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ Rate limiting            │ Not started                                                         │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ CI/CD pipeline           │ Not started                                                         │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ Frontend pages/routing   │ Not started                                                         │
  ├──────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ Admin authorization      │ GET /auth/user_data and DELETE /auth/users/{id} are completely open │
  └──────────────────────────┴─────────────────────────────────────────────────────────────────────┘

  D. Unknown / Unverified Areas

  ┌─────────────────────────────────────────────┬───────────────────────────────────────────────────────────────────┐
  │                    Area                     │                            Why Unknown                            │
  ├─────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Whether Alembic migrations have been        │ Can only be verified by running alembic current inside the        │
  │ applied to the DB                           │ container                                                         │
  ├─────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Whether SMTP is configured and functional   │ Requires valid Gmail App Password in .env                         │
  ├─────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Whether Docker stack runs without errors    │ Requires docker-compose up to verify                              │
  ├─────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ Whether app/core/config.py reads correctly  │ Env var name mismatch with docker-compose; JWT tokens may be      │
  │ from .env                                   │ regenerated on each restart                                       │
  ├─────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ OTP security in practice                    │ OTPs stored as plaintext; no rate limiting on attempts            │
  └─────────────────────────────────────────────┴───────────────────────────────────────────────────────────────────┘

  E. Current Technology Stack

  ┌──────────────────┬──────────────────────────────────────┬─────────────────────────────────────────┐
  │      Layer       │              Technology              │                 Version                 │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Language         │ Python                               │ 3.11                                    │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Web Framework    │ FastAPI                              │ ≥0.139                                  │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ ASGI Server      │ Uvicorn                              │ ≥0.51                                   │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ ORM              │ SQLAlchemy                           │ ≥2.0 (async)                            │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ DB Driver        │ asyncpg                              │ ≥0.29                                   │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Database         │ PostgreSQL                           │ 15 (Docker)                             │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Cache            │ Redis                                │ 7 (Docker, unused in code)              │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Migrations       │ Alembic                              │ ≥1.18                                   │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ JWT              │ python-jose                          │ ≥3.5                                    │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Password Hashing │ pwdlib (bcrypt)                      │ ≥0.3 (active); passlib (legacy, unused) │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Email            │ aiosmtplib                           │ latest                                  │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Validation       │ Pydantic v2 + pydantic-settings      │ ≥2.13                                   │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Package Manager  │ uv (uv.lock present)                 │ —                                       │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Frontend         │ React + TypeScript + Vite            │ 18 / 5 / 5                              │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ CSS              │ Tailwind CSS                         │ 3.4                                     │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Frontend State   │ Zustand (installed, unused)          │ 4.5                                     │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Frontend HTTP    │ Axios (installed, unused)            │ 1.6                                     │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Frontend Routing │ react-router-dom (installed, unused) │ 6.21                                    │
  ├──────────────────┼──────────────────────────────────────┼─────────────────────────────────────────┤
  │ Containerization │ Docker + Docker Compose              │ —                                       │
  └──────────────────┴──────────────────────────────────────┴─────────────────────────────────────────┘

  F. Current Architecture Summary

  The backend follows a clean 4-layer architecture:

  HTTP Request
      ↓
  FastAPI Router (app/api/v1/auth.py)
      ↓
  Service Layer (app/services/)         ← Business logic, orchestration
      ↓
  Repository Layer (app/repositories/)  ← DB access for refresh tokens
      ↓
  SQLAlchemy Models (app/models/)       ← ORM
      ↓
  PostgreSQL (via asyncpg)

  The auth module (registration → OTP → verification → login → JWT) is the only domain that is meaningfully implemented.
  Everything else in the planned architecture (matching, messaging, WebRTC, friendship) does not yet exist in code.

  ---
  G. Files That Should Be Inspected Next (Priority Order)

  1. backend/.env — Verify actual values for DATABASE_URL, SECRET_KEY/JWT_SECRET_KEY, SMTP_*; confirm whether env var
  name mismatch is present in practice
  2. backend/app/core/config.py vs backend/app/config.py — The dual-config structure is the single most likely source of
  runtime bugs; needs to be resolved
  3. backend/app/api/v1/auth.py lines 177-202 — The open GET /auth/user_data and DELETE /auth/users/{id} endpoints with
  no authorization
  4. backend/app/services/otp_service.py — OTP stored as plaintext; create_otp() calls db.commit() inside a function
  that is also called inside a route that already manages commit lifecycle
  5. backend/alembic/versions/748a3a90d846_.py — The third migration removed the ondelete='CASCADE' from the
  otps.user_id FK; verify whether this is intentional
  6. backend/app/models/refresh_token.py line 37 — Uses default=datetime.utcnow (no timezone); the expires_at column
  uses DateTime(timezone=True) — timezone consistency needs verification
  7. backend/tests/ — Needs a full test suite written from scratch
  8. backend/app/websocket/ — Next major feature area to build (Redis Pub/Sub will be needed here)
  9. frontend/src/App.tsx — Needs to be replaced with actual routing and auth UI
  10. docker-compose.yml line 51 — Passes JWT_SECRET_KEY but app/core/config.py reads SECRET_KEY; one of these must
  change