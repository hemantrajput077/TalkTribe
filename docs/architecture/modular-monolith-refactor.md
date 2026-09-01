# TalkTribe --- Modular Monolith Architecture Refactoring Plan

**Status:** Approved direction for architecture refactoring\
**Purpose:** Refactor the existing TalkTribe backend toward a
modular-monolith architecture while preserving all currently working
functionality.

------------------------------------------------------------------------

## 1. Objective

Refactor the current backend from a general layered structure into a
**domain-oriented modular monolith**.

The most important rule is:

> **Do not break or unnecessarily change the currently working
> authentication functionality while restructuring the code.**

This is an architecture refactoring, not a new-feature implementation.

------------------------------------------------------------------------

## 2. Current Direction

The current backend broadly follows:

``` text
API / Router
     ↓
Service
     ↓
Repository
     ↓
SQLAlchemy Model
     ↓
PostgreSQL
```

This is acceptable for the current authentication implementation, but
the project will grow into multiple domains.

The target should therefore organize code primarily by **business/domain
ownership**, while retaining appropriate application, domain,
infrastructure, and API responsibilities inside those boundaries.

------------------------------------------------------------------------

## 3. Target Architecture

Use a **Modular Monolith**.

This means:

-   One backend application initially
-   One deployable backend
-   One codebase
-   PostgreSQL as the durable system of record
-   Redis for infrastructure needs such as Pub/Sub, presence, caching
    and rate limiting
-   Clear domain boundaries
-   Domains communicate through explicit application services/interfaces
-   A domain must not directly access another domain's private
    repository/database implementation

Target high-level structure:

``` text
backend/
└── app/
    ├── api/
    │
    ├── domains/
    │   ├── auth/
    │   ├── profile/
    │   ├── matching/
    │   ├── friendship/
    │   ├── messaging/
    │   ├── presence/
    │   └── admin/
    │
    ├── infrastructure/
    │   ├── database/
    │   ├── redis/
    │   ├── email/
    │   ├── security/
    │   └── config/
    │
    └── shared/
        └── common utilities only
```

Future domains should not be implemented now:

``` text
notifications/
practice_sessions/
voice_video/
communities/
gamification/
ai/
```

------------------------------------------------------------------------

# 4. Domain Responsibilities

## Auth

Owns:

-   Registration
-   OTP generation/verification
-   Login
-   JWT access/refresh tokens
-   Account verification
-   Authentication-related business rules

Auth should not own generic FastAPI request dependencies.

------------------------------------------------------------------------

## Profile

Owns:

-   User profile
-   Bio
-   Profession
-   Location
-   Profile photo
-   Profile-related business rules

------------------------------------------------------------------------

## Matching

Owns:

-   Candidate discovery
-   Matching rules
-   Compatibility calculation
-   Ranking
-   Top-20 recommendation behavior

MVP matching is rule-based.

------------------------------------------------------------------------

## Friendship

Owns:

-   Friend/connection requests
-   Accept/reject
-   Friend relationships
-   Friend removal
-   Blocking
-   Connection-related business rules

------------------------------------------------------------------------

## Messaging

Owns:

-   Conversations
-   Messages
-   Message persistence
-   Message retention
-   Delivery/read state
-   Typing events
-   Messaging rules

------------------------------------------------------------------------

## Presence

Owns:

-   Online/offline state
-   Connection state
-   Presence events
-   Real-time presence behavior

Redis may be used for transient/distributed presence state.

------------------------------------------------------------------------

## Admin

Owns:

-   Administrative operations
-   User management
-   Moderation
-   Other privileged MVP operations

The exact Admin MVP feature set will be implemented only after its
requirements are finalized.

------------------------------------------------------------------------

# 5. Infrastructure Responsibilities

Infrastructure contains technical implementations that support domains.

Examples:

``` text
infrastructure/
├── database/
├── redis/
├── email/
├── security/
└── config/
```

Domains should depend on infrastructure through appropriate interfaces
where useful.

Example:

``` text
Auth
  ↓
Email interface
  ↓
Email adapter
  ↓
SMTP / future provider
```

Auth should not be tightly coupled to a specific email provider.

------------------------------------------------------------------------

# 6. API Responsibility

The API layer owns transport concerns:

-   HTTP routing
-   WebSocket routing
-   Request/response handling
-   FastAPI dependencies
-   Authentication extraction
-   API versioning
-   HTTP error mapping

Authentication dependency such as `get_current_user()` should be
available from the API/security boundary rather than forcing every
future domain to import it from the Auth service.

Conceptually:

``` text
Request
   ↓
API Authentication Dependency
   ↓
Current User
   ↓
Domain Route
   ↓
Application Service
```

------------------------------------------------------------------------

# 7. Domain Internal Structure

Each domain should use a consistent internal structure where justified.

Example:

``` text
domains/
└── profile/
    ├── api/
    ├── application/
    ├── domain/
    ├── infrastructure/
    └── schemas/
```

Meaning:

``` text
api/
    Transport/API entry points

application/
    Use cases and transaction boundaries

domain/
    Business rules and domain concepts

infrastructure/
    Persistence/adapters owned by the domain

schemas/
    API/input/output contracts where appropriate
```

Do not create unnecessary layers or files just to satisfy a template.

------------------------------------------------------------------------

# 8. Database Rules

PostgreSQL remains the primary durable data store.

Each domain should have clear ownership of its database models/tables.

Rules:

1.  A domain owns its persistence model.
2.  Other domains must not directly modify another domain's repository.
3.  Cross-domain operations should use application/domain contracts.
4.  Foreign keys and relationships must be designed deliberately.
5.  Transactions should be controlled at the
    application/service/use-case boundary.
6.  Avoid arbitrary commits inside lower-level repositories.
7.  Do not create a second database engine/session system.

------------------------------------------------------------------------

# 9. Redis Rules

Redis is not the primary database.

Use Redis only where its capabilities are appropriate:

-   Pub/Sub
-   Presence
-   Caching
-   Rate limiting
-   Distributed coordination where required

Do not add Redis usage merely because Redis exists in Docker.

The current refactor should establish a clean Redis infrastructure
boundary without prematurely implementing the complete
messaging/presence system.

------------------------------------------------------------------------

# 10. Critical Refactoring Rule --- Preserve Current Functionality

The existing authentication functionality must continue to work.

Before refactoring, establish a baseline for:

``` text
POST /api/v1/auth/register
POST /api/v1/auth/verify-otp
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Use the actual endpoint names from the repository if they differ.

The following behavior must remain functional:

``` text
Register
   ↓
OTP generated
   ↓
OTP persisted
   ↓
OTP verified
   ↓
Account becomes verified
   ↓
Login
   ↓
JWT access/refresh tokens
   ↓
Protected endpoint access
   ↓
Refresh token flow
   ↓
Logout/revocation behavior
```

Do not change externally visible behavior unless a change is explicitly
required for a security fix.

------------------------------------------------------------------------

# 11. Refactor Safety Rules

Claude/developer must follow these rules:

### Rule 1 --- Inspect before changing

Before modifying code:

-   Inspect the current repository.
-   Identify all imports and dependencies.
-   Identify all authentication routes.
-   Identify all authentication services.
-   Identify all repositories/models/schemas.
-   Identify configuration and database implementations.
-   Identify migrations.
-   Identify tests or manual verification procedures.

Do not guess.

### Rule 2 --- Do not rewrite

Move/refactor existing code incrementally.

Do not rewrite the authentication system from scratch.

### Rule 3 --- Preserve API contracts

Existing endpoint paths, request structures and response structures
should remain unchanged unless explicitly approved.

### Rule 4 --- Preserve database behavior

Do not rename/drop/change existing tables or columns merely for
architectural cleanliness.

If a database change is necessary, create an Alembic migration and
explain why.

### Rule 5 --- One infrastructure implementation

Consolidate duplicate configuration/database implementations into one
canonical implementation.

Do not keep two active implementations "temporarily" without a clear
migration plan.

### Rule 6 --- No new product features

Do not implement:

-   Profile
-   Matching
-   Friendship
-   Messaging
-   Presence
-   Admin features

during this architecture-only refactor.

Only create the structural boundaries required to support them later.

### Rule 7 --- No premature infrastructure

Do not introduce:

-   Microservices
-   Kafka
-   Kubernetes
-   complex event buses
-   AI infrastructure
-   WebRTC
-   notification infrastructure

as part of this refactor.

------------------------------------------------------------------------

# 12. Required Refactoring Sequence

Follow this order:

``` text
1. Inspect current repository
        ↓
2. Establish authentication baseline
        ↓
3. Identify duplicate infrastructure
        ↓
4. Create target directories
        ↓
5. Create canonical config infrastructure
        ↓
6. Create canonical database infrastructure
        ↓
7. Move Auth into domains/auth
        ↓
8. Move authentication-related schemas/models/repositories/services
        ↓
9. Move shared security mechanisms to appropriate infrastructure/API boundary
        ↓
10. Update imports
        ↓
11. Remove obsolete duplicate implementations
        ↓
12. Run migrations/check schema compatibility
        ↓
13. Run backend checks
        ↓
14. Verify all authentication flows
        ↓
15. Review diff
        ↓
16. Document changes
```

------------------------------------------------------------------------

# 13. Suggested Auth Target Structure

Use the actual existing files as the source of truth, but the intended
direction is:

``` text
domains/
└── auth/
    ├── api/
    │   └── routes.py
    │
    ├── application/
    │   └── auth_service.py
    │
    ├── domain/
    │   ├── entities.py
    │   └── rules.py
    │
    ├── infrastructure/
    │   ├── repository.py
    │   └── token_repository.py
    │
    └── schemas/
        └── auth.py
```

Do not force existing files into this exact layout if doing so creates
unnecessary churn. Preserve behavior and use judgment.

------------------------------------------------------------------------

# 14. Configuration

There must be one canonical configuration system.

It should be responsible for:

-   Database URL
-   JWT configuration
-   OTP configuration
-   Redis configuration
-   Email configuration
-   Environment-specific settings

Rules:

-   No duplicated settings classes.
-   No duplicated environment-variable naming.
-   No hard-coded secrets.
-   No accidental mismatch between configuration names and `.env`.
-   Secrets must never be committed.

------------------------------------------------------------------------

# 15. Database Infrastructure

There must be one canonical database setup:

``` text
infrastructure/database/
├── base.py
├── session.py
└── dependencies.py
```

The exact filenames may differ if the current project already has a
better naming convention.

Requirements:

-   One SQLAlchemy engine
-   One session factory
-   One canonical session dependency
-   One declarative Base
-   Alembic uses the canonical metadata
-   No duplicate database engines/session systems

------------------------------------------------------------------------

# 16. Security

During this refactor, security problems discovered in the current
implementation must not be preserved merely for architectural
consistency.

At minimum review:

-   OTP plaintext storage
-   JWT configuration consistency
-   Authentication dependency placement
-   Protected user-data endpoints
-   Account deletion authorization
-   Password hashing
-   Secret handling
-   Refresh-token behavior

If a security change changes existing behavior, document it explicitly.

------------------------------------------------------------------------

# 17. Testing / Verification

Before refactoring:

``` text
Record current behavior
```

After every meaningful refactoring step:

``` text
Import checks
↓
Application startup
↓
Database connection
↓
Alembic check
↓
API health
↓
Authentication flow
```

At minimum verify:

``` text
Register → OTP → Verify → Login → Protected endpoint
```

Also verify:

``` text
Refresh token
Logout/revocation
Invalid OTP
Invalid credentials
Unauthorized protected endpoint
```

The architecture refactor is **not complete** if authentication no
longer works.

------------------------------------------------------------------------

# 18. Definition of Done

The architecture refactor is complete when:

-   [ ] Modular-monolith structure exists.
-   [ ] Auth is located inside its domain boundary.
-   [ ] One canonical configuration system exists.
-   [ ] One canonical database system exists.
-   [ ] Duplicate infrastructure is removed.
-   [ ] Existing API contracts are preserved.
-   [ ] Existing authentication behavior works.
-   [ ] Database schema remains compatible.
-   [ ] Alembic works.
-   [ ] Application starts successfully.
-   [ ] Authentication flow is manually/API tested.
-   [ ] Security issues found during refactor are addressed or
    explicitly tracked.
-   [ ] No new product feature was accidentally introduced.
-   [ ] No microservice architecture was introduced.
-   [ ] Documentation reflects the actual resulting structure.
-   [ ] A PR/diff review confirms only intended changes were made.

------------------------------------------------------------------------

# 19. Git / Change Strategy

Do this refactor in small commits.

Recommended:

``` text
Commit 1:
Create target domain/infrastructure structure

Commit 2:
Consolidate configuration

Commit 3:
Consolidate database infrastructure

Commit 4:
Move Auth domain

Commit 5:
Move security/API dependencies

Commit 6:
Remove obsolete duplicate infrastructure

Commit 7:
Tests/fixes/documentation
```

Keep commits focused and easy to review.

Do not combine this architecture refactor with Profile/Matching/Chat
implementation.

------------------------------------------------------------------------

# 20. Claude Instructions

Use this document as the implementation contract.

Claude must:

1.  Inspect the current repository before editing.
2.  Compare the current structure against this target.
3.  Identify exact files that need to move/change.
4.  Present the proposed migration plan before making large changes.
5.  Preserve current authentication behavior.
6.  Make changes incrementally.
7.  Run verification after each major step.
8.  Report any behavior change explicitly.
9.  Never invent missing requirements.
10. Never implement future product features.
11. Never introduce microservices.
12. Never delete code unless its replacement is verified.
13. Update imports/references after moves.
14. Check Alembic/database compatibility.
15. Provide a final summary of:

-   files moved
-   files changed
-   files deleted
-   behavior preserved
-   tests/checks executed
-   remaining issues

------------------------------------------------------------------------

# 21. Expected Result

After this refactor, the project should conceptually become:

``` text
                 TalkTribe Backend
                        │
                Modular Monolith
                        │
       ┌────────────────┼─────────────────┐
       │                │                 │
      Auth           Profile          Matching
       │                │                 │
 Friendship         Messaging        Presence
       │                │                 │
       └────────────────┼─────────────────┘
                        │
                      Admin
                        │
              ┌─────────┴─────────┐
              │                   │
         PostgreSQL             Redis
```

The important outcome is not the folder names.

The important outcome is:

> **Each business domain has clear ownership, infrastructure is
> centralized, and the existing authentication system continues to
> work.**

------------------------------------------------------------------------

# 22. After This Refactor

Do not immediately implement all features.

Next architecture steps:

``` text
Modular Monolith Refactor
        ↓
Domain Boundaries
        ↓
Component Architecture
        ↓
Database Architecture
        ↓
API Architecture
        ↓
Security Architecture
        ↓
Realtime Architecture
        ↓
Target Architecture Finalization
        ↓
Feature Workflows
        ↓
Jira Stories
```

This refactor is therefore the **foundation**, not the complete
TalkTribe architecture implementation.
