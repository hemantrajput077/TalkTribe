# TalkTribe — EPIC-00 Jira Stories

**Epic:** EPIC-00 — Engineering Foundation  
**Milestone:** M0 — Engineering Baseline  
**Scope:** MVP  
**Priority:** Critical  
**Status:** Jira-ready story baseline

**Primary references:**
- `TARGET_ARCHITECTURE.md`
- `FEATURE_DEPENDENCIES.md`
- `DEVELOPMENT_ROADMAP.md`
- `FEATURE_CATALOG.md`
- `EPIC_CATALOG.md`
- `JIRA_GENERATION_RULES.md`

> Note: These stories define the required target behavior. Before implementation, verify the current repository and remove any task that is already fully satisfied.

---

# Story 1 — Consolidate Application Configuration

## Suggested Jira Title

**Consolidate backend application configuration**

## Feature ID

`ENG-01`

## Epic

`EPIC-00 — Engineering Foundation`

## Priority

Critical

## User / System Story

As the TalkTribe backend,
I need one authoritative configuration system,
so that all environments use consistent database, JWT, Redis, email, storage, CORS, and logging settings.

## Business Context

Every later backend feature depends on predictable configuration.

Duplicate or conflicting configuration can create:

- inconsistent secrets
- unstable authentication
- incorrect database connections
- environment-specific failures
- difficult debugging

## In Scope

- identify all active configuration implementations
- select one canonical configuration module
- consolidate database configuration
- consolidate JWT configuration
- consolidate Redis configuration
- consolidate email configuration
- define storage configuration boundary
- define CORS configuration
- define environment selection
- define logging-related configuration
- remove or deprecate duplicate active configuration paths
- fail clearly when required production configuration is missing

## Out of Scope

- AWS Secrets Manager migration
- SSM integration
- production deployment
- feature-specific business configuration
- notification configuration

## Dependencies

None.

## Architecture References

- `TARGET_ARCHITECTURE.md`
- `SECURITY_ARCHITECTURE.md`
- `COMPONENT_ARCHITECTURE.md`

## Acceptance Criteria

### AC1 — One configuration source

Given the backend starts,
when application configuration is loaded,
then one authoritative configuration object/module is used by the application.

### AC2 — JWT secret consistency

Given a configured JWT secret,
when tokens are created and later validated,
then both operations use the same configured secret.

### AC3 — Required production secrets

Given the application is running in a production environment,
when a required security setting such as the JWT secret is missing,
then startup fails clearly instead of generating an unsafe random replacement.

### AC4 — Infrastructure configuration

Given database, Redis, and email settings are configured,
when their infrastructure adapters initialize,
then they read configuration from the canonical configuration system.

### AC5 — Duplicate active config removed

Given the repository previously contained duplicate active configuration paths,
when this Story is completed,
then runtime code no longer depends on conflicting configuration implementations.

## Technical Notes

Prefer environment-backed typed settings.

Do not introduce service-specific configuration directly inside domain modules.

## API Impact

None expected.

## Database Impact

None.

## Security

- secrets must not be logged
- production must not silently use insecure defaults
- JWT secret behavior must be deterministic

## Test Requirements

- configuration loads valid environment
- missing required production secret fails
- JWT encode/decode use same configuration
- test environment can override required infrastructure values
- duplicate runtime configuration imports are eliminated or intentionally isolated

## Definition of Done

- acceptance criteria pass
- configuration tests pass
- affected imports are migrated
- dead configuration path is removed or clearly deprecated
- no secrets appear in logs

---

# Story 2 — Consolidate Database and Session Infrastructure

## Suggested Jira Title

**Consolidate SQLAlchemy engine and session management**

## Feature ID

`ENG-02`

## Priority

Critical

## User / System Story

As the TalkTribe backend,
I need one database engine and session-management implementation,
so that all domains use consistent connections, transactions, and request-scoped sessions.

## Business Context

Duplicate database/session implementations create hidden transaction behavior and make future modular domains unreliable.

## In Scope

- identify active SQLAlchemy engine/session implementations
- establish one canonical engine
- establish one canonical async session factory
- establish one request-scoped database dependency
- document transaction ownership expectations
- migrate active imports
- remove/deprecate duplicate active DB infrastructure
- ensure Alembic uses compatible metadata/configuration

## Out of Scope

- creating feature tables
- database-provider migration
- production backup implementation
- performance tuning beyond obvious correctness issues

## Dependencies

- `ENG-01` canonical configuration

## Acceptance Criteria

### AC1 — Single engine

Given the application initializes database infrastructure,
when runtime code requests the database engine,
then one canonical engine implementation is used.

### AC2 — Single session factory

Given an API request requires database access,
when a session is provided,
then it comes from the canonical async session factory.

### AC3 — Request cleanup

Given a request completes or fails,
when its database dependency exits,
then the session is closed correctly.

### AC4 — Transaction ownership

Given an application use case modifies multiple records,
when the operation succeeds,
then the application/use-case layer controls the commit.

Given one operation fails,
then related writes are rolled back together.

### AC5 — Duplicate infrastructure removed

Runtime business code must not import multiple competing DB/session modules.

## Technical Notes

Repositories should not independently commit unless an explicitly approved exception exists.

## API Impact

None externally.

## Database Impact

No new product schema expected.

Alembic configuration may be updated to use the canonical metadata path.

## Security

Database credentials must come through canonical configuration and must not be logged.

## Test Requirements

- request session opens/closes correctly
- rollback occurs on failed multi-write use case
- commit occurs once at application boundary
- canonical engine/session imports are used
- Alembic environment still loads metadata successfully

## Definition of Done

- one active engine
- one active session factory
- one DB dependency
- transaction convention documented
- tests pass
- duplicate runtime DB infrastructure removed/deprecated

---

# Story 3 — Consolidate Password and JWT Security Utilities

## Suggested Jira Title

**Consolidate password hashing and JWT security utilities**

## Feature ID

`ENG-03`

## Priority

Critical

## User / System Story

As the TalkTribe authentication system,
I need one canonical security implementation,
so that passwords and JWTs are handled consistently and safely across the application.

## Business Context

Multiple password or JWT implementations can cause authentication incompatibility and security defects.

## In Scope

- identify active password-hashing implementations
- select canonical password hash/verify path
- identify active JWT helpers
- select canonical token encode/decode path
- migrate Auth to canonical utilities
- remove/deprecate unused competing implementations
- preserve existing valid password compatibility where required
- ensure token validation uses canonical configuration

## Out of Scope

- MFA
- OAuth/Google login
- refresh-token business workflow changes beyond utility integration
- password-reset feature

## Dependencies

- `ENG-01` configuration consolidation

## Acceptance Criteria

### AC1 — Password hashing

Given a new password is stored,
when hashing occurs,
then the canonical password utility is used.

### AC2 — Password verification

Given a valid existing password hash supported by the application,
when the correct password is verified,
then authentication succeeds.

### AC3 — Wrong password

Given an incorrect password,
when verification occurs,
then verification fails without exposing hash details.

### AC4 — JWT creation

Given an authenticated identity,
when an access token is created,
then the canonical JWT utility and configured signing secret are used.

### AC5 — JWT validation

Given a valid application token,
when it is decoded,
then the canonical JWT validation path accepts it.

Expired/invalid tokens must be rejected.

## Technical Notes

If both `pwdlib` and `passlib` currently exist, verify which one is active before removal.

Do not break existing stored password hashes without a migration/compatibility plan.

## API Impact

Existing Auth API behavior should remain compatible.

## Database Impact

None expected.

## Security

- never log raw passwords
- never log token contents unnecessarily
- reject invalid/expired signatures
- do not introduce random production signing secrets

## Test Requirements

- hash + verify correct password
- reject incorrect password
- create + validate JWT
- reject expired JWT
- reject tampered JWT
- verify existing password compatibility if relevant

## Definition of Done

- canonical password utility established
- canonical JWT utility established
- active Auth uses them
- duplicate/dead security path removed/deprecated
- regression/security tests pass

---

# Story 4 — Establish Reliable Backend Test Infrastructure

## Suggested Jira Title

**Establish backend automated test foundation**

## Feature ID

`ENG-04`

## Priority

Critical

## User / System Story

As a developer,
I need a repeatable backend test environment,
so that refactoring and feature development can proceed without silently breaking existing behavior.

## Business Context

Auth already has implemented behavior that must be protected before deeper refactoring and new domains are added.

## In Scope

- standardize pytest configuration
- configure async tests
- establish FastAPI test client pattern
- establish database-test fixtures
- define transaction/data cleanup strategy
- define integration-test conventions
- add shared test factories/helpers only where useful
- ensure tests can run from documented command
- prepare real PostgreSQL integration path for DB-specific behavior

## Out of Scope

- full test coverage for every future feature
- complete end-to-end browser suite
- load testing
- production monitoring

## Dependencies

- `ENG-01`
- `ENG-02`

## Acceptance Criteria

### AC1 — Repeatable execution

Given a developer checks out the project with required dependencies,
when the documented test command is run,
then the backend test suite starts reliably.

### AC2 — Async support

Given an async application/service test,
when pytest executes it,
then async FastAPI/SQLAlchemy behavior is supported.

### AC3 — Database isolation

Given one test writes database data,
when the next independent test runs,
then it does not accidentally depend on previous test state.

### AC4 — API test support

Given an API endpoint needs testing,
then the test infrastructure supports authenticated/unauthenticated HTTP requests.

### AC5 — PostgreSQL path

DB-specific constraints/concurrency behavior must have a path to real PostgreSQL testing rather than relying only on SQLite behavior.

## Technical Notes

SQLite may be used for isolated lightweight tests where appropriate, but must not be treated as equivalent for PostgreSQL-specific semantics.

## API Impact

None.

## Database Impact

Test-only infrastructure/configuration.

## Security

Test secrets must be non-production and isolated.

## Test Requirements

This Story is the test infrastructure itself.

Add at least a smoke test proving:

- app startup/test client
- DB session
- async test execution

## Definition of Done

- documented test command works
- async tests work
- API tests work
- DB isolation works
- PostgreSQL integration strategy is documented/usable
- CI can later invoke same suite

---

# Story 5 — Standardize API Error Handling

## Suggested Jira Title

**Standardize API error response conventions**

## Feature ID

`ENG-05`

## Priority

High

## User / System Story

As a frontend/client developer,
I need predictable backend error responses,
so that the application can handle validation, authorization, conflicts, and business errors consistently.

## Business Context

Different domains will soon expose many APIs. Without an error contract, frontend and tests become inconsistent.

## In Scope

- define standard error response shape
- define stable application error codes
- map business exceptions to HTTP responses
- distinguish validation, authentication, authorization, conflict, not-found, and server errors
- integrate conventions with FastAPI exception handling
- migrate critical Auth errors where practical
- prevent internal exception details from leaking to clients

## Out of Scope

- defining every future domain error code now
- frontend toast design
- observability platform selection

## Dependencies

- `ENG-01`
- stable FastAPI application setup

## Recommended Error Shape

Example:

```json
{
  "error": {
    "code": "PROFILE_INCOMPLETE",
    "message": "Complete your profile before using this feature."
  }
}
```

Optional correlation/request ID may be added.

## Acceptance Criteria

### AC1 — Validation

Invalid request data returns an appropriate 4xx response without internal stack details.

### AC2 — Authentication

Missing/invalid authentication returns consistent authentication error structure.

### AC3 — Authorization

Authenticated user lacking permission receives a consistent forbidden response.

### AC4 — Conflict

Duplicate or conflicting business state can return a stable error code.

### AC5 — Internal failures

Unexpected internal exceptions do not expose stack traces, SQL, secrets, or implementation details to clients.

## API Impact

Defines shared error contract across APIs.

## Database Impact

None.

## Security

Never expose:

- SQL
- passwords
- tokens
- secrets
- stack traces in production responses

## Test Requirements

- validation error
- unauthorized error
- forbidden error
- conflict example
- not-found example
- internal exception sanitization

## Definition of Done

- error schema documented
- exception mapping implemented
- critical endpoints follow convention
- tests pass
- no sensitive exception details leak

---

# Story 6 — Establish CI Quality Gates

## Suggested Jira Title

**Add automated CI quality gates for backend changes**

## Feature ID

`ENG-06`

## Priority

High

## User / System Story

As a developer,
I need automated checks on every pull request,
so that tests, linting, typing, and security checks catch regressions before merge.

## Business Context

As the project grows into multiple domains, relying only on manual local checks will increase regressions and inconsistent code quality.

## In Scope

Verify and/or configure CI to run:

```text
tests
ruff
mypy
bandit
```

Optionally:

```text
Alembic migration validation
build/import smoke test
```

Use the same commands developers can run locally.

## Out of Scope

- production deployment itself
- expensive load tests on every PR
- frontend CI unless included in the same implementation slice
- full SAST platform integration

## Dependencies

- `ENG-04` test foundation
- stable project dependency installation

## Acceptance Criteria

### AC1 — Pull request checks

Given a pull request changes backend code,
when CI runs,
then required backend quality checks execute automatically.

### AC2 — Test failure

Given an automated test fails,
then the CI job fails.

### AC3 — Lint failure

Given Ruff finds a configured blocking violation,
then the relevant CI job fails.

### AC4 — Type failure

Given Mypy reports a configured blocking type issue,
then the relevant CI job fails.

### AC5 — Security failure

Given Bandit reports a configured blocking security issue,
then the security check fails according to the agreed threshold/configuration.

### AC6 — Reproducibility

CI commands are documented and can be executed locally.

## Technical Notes

If `.github/workflows/` already contains CI, inspect it first and modify only the missing or inconsistent parts.

Do not duplicate working workflows unnecessarily.

## API Impact

None.

## Database Impact

Potential test database service only.

## Security

CI logs must not print secrets.

Secrets used for tests must be non-production.

## Test Requirements

Validate CI with a normal successful run and confirm expected failure behavior through configuration/review.

## Definition of Done

- required checks run on PRs
- failed checks block/flag merge according to repository policy
- commands match local development
- CI documentation exists
- no production secrets are exposed

---

# Suggested Jira Creation Order

Create these Stories in this order because later work depends on the earlier foundation:

```text
1. Consolidate backend application configuration          [ENG-01]
2. Consolidate SQLAlchemy engine and session management   [ENG-02]
3. Consolidate password hashing and JWT utilities         [ENG-03]
4. Establish backend automated test foundation            [ENG-04]
5. Standardize API error response conventions             [ENG-05]
6. Add automated CI quality gates                         [ENG-06]
```

Some can overlap after the initial repository audit.

---

# Dependency View

```text
ENG-01 Configuration
   ├──────────────┐
   ▼              ▼
ENG-02 DB      ENG-03 Security
   │              │
   └──────┬───────┘
          ▼
       ENG-04 Tests
          │
    ┌─────┴─────┐
    ▼           ▼
ENG-05 Errors  ENG-06 CI
```

---

# Jira Epic Description — Ready to Copy

## Epic Name

**Engineering Foundation**

## Planning ID

`EPIC-00`

## Milestone

`M0 — Engineering Baseline`

## Business Outcome

Create a stable, testable, and secure application foundation before additional TalkTribe domains are implemented.

## Scope

- canonical configuration
- canonical DB/session infrastructure
- canonical security utilities
- automated test foundation
- API error conventions
- CI quality gates

## Out of Scope

- new product features
- voice calling
- matching
- profile
- production deployment

## Completion Criteria

- one authoritative configuration path
- one DB/session path
- one password/JWT implementation
- repeatable automated tests
- consistent API error handling
- automated CI quality gates

---

# Next Epic

After EPIC-00 reaches the required baseline:

```text
EPIC-01 — Authentication & Account Security
```

That Epic should preserve current working Auth behavior while resolving the known security and architectural issues.
