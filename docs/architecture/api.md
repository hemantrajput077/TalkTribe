# TalkTribe API Architecture

**Status:** Stage 2 architecture design  
**Architecture style:** Modular Monolith  
**API framework:** FastAPI  
**API version:** `/api/v1`  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `DOMAIN_BOUNDARIES.md`, `COMPONENT_ARCHITECTURE.md`, `DATABASE_ARCHITECTURE.md`

---

## 1. Purpose

This document defines how clients interact with the TalkTribe backend.

It establishes:

- API ownership by domain
- REST conventions
- API versioning
- authentication and authorization boundaries
- request/response validation
- error handling
- pagination
- idempotency expectations
- endpoint naming
- WebSocket vs REST responsibilities
- admin API separation
- API testing expectations
- compatibility rules

This document does not define the full realtime event protocol. That belongs in `REALTIME_ARCHITECTURE.md`.

---

# 2. API Principles

1. Use REST for durable request/response business operations.
2. Use WebSockets for realtime events and signaling.
3. Keep routes thin.
4. Business logic belongs in application/domain services.
5. Authentication identifies the caller.
6. Authorization determines whether the caller may perform the operation.
7. Each endpoint belongs to exactly one domain.
8. API schemas are separate from ORM/database models.
9. Never return raw SQLAlchemy models directly from routes.
10. Use consistent error shapes.
11. Paginate list endpoints.
12. Version the API under `/api/v1`.
13. Avoid exposing infrastructure details through API contracts.
14. Preserve backward compatibility where practical.

---

# 3. API Entry Structure

Recommended structure:

```text
app/
├── api/
│   ├── router.py
│   ├── dependencies.py
│   ├── errors.py
│   └── v1/
│
└── domains/
    ├── auth/api/
    ├── profile/api/
    ├── language/api/
    ├── matching/api/
    ├── friendship/api/
    ├── messaging/api/
    ├── calls/api/
    └── admin/api/
```

The application should expose one top-level router.

Conceptually:

```text
main.py
  ↓
api/router.py
  ↓
domain routers
```

---

# 4. API Versioning

All production API endpoints should be mounted under:

```text
/api/v1
```

Examples:

```text
/api/v1/auth/register
/api/v1/profile/me
/api/v1/matches
/api/v1/friends/requests
/api/v1/conversations
/api/v1/calls
/api/v1/admin/users
```

Avoid placing production endpoints directly on the FastAPI application outside the router/version system.

The existing hardcoded `/api/v1/ping` pattern should be normalized into the router structure or treated as a dedicated health endpoint.

---

# 5. Route Naming Conventions

Use lowercase kebab-case for multi-word path segments.

Good:

```text
/verify-email
/resend-otp
/logout-all
/friend-requests
/call-history
```

Avoid:

```text
/user_data
/friendRequests
/VerifyEmail
```

Resource collections should generally use plural nouns:

```text
/users
/profiles
/friends
/conversations
/messages
/calls
/reports
```

Use verbs only when representing a real action that does not map naturally to CRUD.

Examples:

```text
POST /auth/login
POST /auth/logout
POST /friend-requests/{id}/accept
POST /calls/{id}/accept
POST /admin/users/{id}/suspend
```

---

# 6. Authentication API

Base path:

```text
/api/v1/auth
```

Recommended MVP endpoints:

```text
POST /auth/register
POST /auth/verify-email
POST /auth/resend-otp
POST /auth/login
POST /auth/refresh
POST /auth/logout
POST /auth/logout-all
GET  /auth/me
```

Future:

```text
POST /auth/forgot-password
POST /auth/reset-password
POST /auth/change-password
```

### Notes

- `/auth/me` should return authenticated identity/account information, not the complete public profile.
- Public profile data should be owned by Profile.
- Any current dev-only user-list/delete endpoints under Auth should be removed or moved into protected Admin APIs.

---

# 7. Profile API

Base path:

```text
/api/v1/profiles
```

Recommended endpoints:

```text
GET   /profiles/me
PUT   /profiles/me
PATCH /profiles/me
GET   /profiles/{user_id}
```

Possible profile-photo workflow:

```text
POST   /profiles/me/photo
DELETE /profiles/me/photo
```

Only authenticated users may access protected profile endpoints.

Visibility decision:

```text
Authenticated co-learner → may view another user's permitted profile
Admin → may view according to admin policy
Unauthenticated user → denied
```

Exact field-level visibility belongs in `SECURITY_ARCHITECTURE.md`.

---

# 8. Language API

Base path:

```text
/api/v1/languages
```

Recommended endpoints:

```text
GET /languages
GET /languages/{id}
```

User-language management may belong under Profile:

```text
GET  /profiles/me/languages
PUT  /profiles/me/languages
```

or under Language:

```text
GET  /user-languages/me
PUT  /user-languages/me
```

Preferred MVP direction:

Keep user-facing language configuration under Profile while Language owns validation/master data internally.

This keeps the client-facing profile workflow simple.

---

# 9. Matching API

Base path:

```text
/api/v1/matches
```

Recommended endpoint:

```text
GET /matches
```

Optional query parameters:

```text
limit
country
proficiency
interest
```

MVP rules:

- authentication required
- rule-based matching
- maximum 20 results
- exclude blocked/ineligible users
- do not expose sensitive/private account fields

Example response shape:

```json
{
  "items": [
    {
      "user_id": 123,
      "display_name": "Example",
      "profile_photo_url": null,
      "proficiency_level": "B1",
      "shared_interests": ["Photography", "Chess"],
      "compatibility_score": 82
    }
  ],
  "count": 1
}
```

The exact compatibility formula remains a Matching-domain concern.

---

# 10. Friendship API

Base path:

```text
/api/v1/friends
```

Recommended endpoints:

```text
GET    /friends
POST   /friends/requests
GET    /friends/requests
POST   /friends/requests/{request_id}/accept
POST   /friends/requests/{request_id}/reject
DELETE /friends/requests/{request_id}
DELETE /friends/{friend_user_id}
POST   /friends/blocks
DELETE /friends/blocks/{user_id}
```

Alternative route grouping may separate:

```text
/friend-requests
/blocks
```

The important requirement is consistency, not the exact pluralization choice.

All operations must enforce:

- authenticated identity
- target user validity
- block rules
- maximum friend rule
- request state validity

---

# 11. Messaging API

REST should handle durable conversation/message retrieval.

Base path:

```text
/api/v1/conversations
```

Recommended endpoints:

```text
GET  /conversations
POST /conversations
GET  /conversations/{conversation_id}
GET  /conversations/{conversation_id}/messages
```

Sending messages should primarily happen over WebSocket for realtime UX.

A REST fallback may be provided if a concrete requirement appears, but should not create duplicate business logic.

Message history endpoint must be paginated.

Because message retention is one week, APIs must not imply historical availability beyond that policy.

---

# 12. Voice Call API

Voice calling is an MVP capability.

REST should manage durable call operations/history where appropriate.

Base path:

```text
/api/v1/calls
```

Recommended REST endpoints:

```text
GET  /calls
GET  /calls/{call_id}
POST /calls
POST /calls/{call_id}/accept
POST /calls/{call_id}/reject
POST /calls/{call_id}/cancel
POST /calls/{call_id}/end
```

However, realtime call signaling should use WebSocket events.

REST responsibilities:

- create/initiate durable call intent where desired
- retrieve call history
- retrieve call metadata
- perform idempotent call-state operations where appropriate

WebSocket responsibilities:

- incoming-call event
- call ringing
- accept/reject event propagation
- WebRTC offer
- WebRTC answer
- ICE candidates
- realtime call-state notifications

The backend authorizes signaling; the WebRTC media stream remains peer-to-peer.

---

# 13. Rating / Feedback API

The post-call flow includes rating/reporting.

Recommended endpoints:

```text
POST /calls/{call_id}/feedback
GET  /profiles/{user_id}/rating
POST /reports
```

Example feedback request:

```json
{
  "rating": 4,
  "feedback": "Good conversation partner."
}
```

Exact rating range and feedback visibility should be finalized before implementation.

Reports belong to moderation/Admin workflows even when created by regular users.

---

# 14. Admin API

Base path:

```text
/api/v1/admin
```

All Admin endpoints require:

```text
authenticated user
+
ADMIN role
+
action-level authorization
```

Possible MVP endpoints:

```text
GET  /admin/users
GET  /admin/users/{user_id}
POST /admin/users/{user_id}/suspend
POST /admin/users/{user_id}/activate
GET  /admin/reports
GET  /admin/reports/{report_id}
POST /admin/reports/{report_id}/resolve
```

If deletion is supported:

```text
DELETE /admin/users/{user_id}
```

must be heavily protected and audited.

Never expose Admin functionality through unprotected convenience endpoints.

---

# 15. HTTP Method Conventions

Use:

```text
GET     → retrieve
POST    → create/action
PUT     → replace complete resource
PATCH   → partial update
DELETE  → remove
```

Examples:

```text
POST   /friends/requests
PATCH  /profiles/me
DELETE /friends/{id}
```

Avoid using `GET` for state-changing operations.

---

# 16. HTTP Status Code Conventions

Recommended:

```text
200 OK
201 Created
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Entity
429 Too Many Requests
500 Internal Server Error
503 Service Unavailable
```

Examples:

```text
POST /auth/register
→ 201 Created

DELETE /friends/{id}
→ 204 No Content

invalid login
→ 401 Unauthorized

authenticated but not allowed
→ 403 Forbidden

duplicate username
→ 409 Conflict

rate-limited OTP resend
→ 429 Too Many Requests
```

---

# 17. Authentication Dependency

The FastAPI bearer/token dependency belongs in the API/transport layer.

Recommended conceptual location:

```text
app/api/dependencies.py
```

Example responsibilities:

```text
get_current_identity()
require_authenticated_user()
require_admin()
```

These functions should delegate token verification to Auth/security components.

Future routers should not need to import implementation details from `auth_service.py`.

---

# 18. Authorization

Route-level checks are the first gate.

Application services must enforce business authorization.

Example:

```text
DELETE /friends/{user_id}
        ↓
authenticate caller
        ↓
Friendship application service
        ↓
verify relationship ownership/state
        ↓
perform removal
```

Do not trust route protection alone for sensitive domain operations.

---

# 19. Request Validation

Pydantic handles API-boundary validation.

Examples:

```text
required fields
length
format
enum values
basic string constraints
```

Business rules belong in application/domain services.

Example:

Pydantic:

```text
rating must be integer
rating between 1 and 5
```

Domain/application:

```text
reviewer may rate only a completed call they participated in
```

Do not put cross-resource business rules into Pydantic schemas.

---

# 20. Response Schemas

Always use explicit response schemas.

Never return:

```text
raw User ORM model
raw SQLAlchemy query result
password hash
OTP hash
refresh token record
internal moderation metadata
```

Use dedicated views:

```text
AuthenticatedIdentityResponse
PublicProfileResponse
AdminUserResponse
MatchCandidateResponse
ConversationResponse
MessageResponse
CallResponse
```

Different audiences may require different response models.

---

# 21. Standard Success Response Philosophy

Do not wrap every successful response unnecessarily.

For a resource:

```json
{
  "id": 123,
  "username": "learner"
}
```

For collections:

```json
{
  "items": [],
  "pagination": {
    "limit": 20,
    "next_cursor": null
  }
}
```

For command endpoints returning no useful body:

```text
204 No Content
```

Use consistency over decorative response wrappers.

---

# 22. Standard Error Format

Recommended common shape:

```json
{
  "error": {
    "code": "FRIEND_LIMIT_REACHED",
    "message": "You have reached the maximum friend limit.",
    "details": null,
    "request_id": "optional-trace-id"
  }
}
```

Fields:

```text
code       → stable machine-readable identifier
message    → user/developer-readable description
details    → optional validation/context
request_id → observability correlation
```

Do not make frontend logic depend on arbitrary free-text `detail` strings.

---

# 23. Error Mapping

Application/domain errors should map to HTTP at the API boundary.

Examples:

```text
InvalidCredentials
→ 401

AccountSuspended
→ 403

ProfileNotFound
→ 404

FriendRequestAlreadyExists
→ 409

FriendLimitReached
→ 409

UserBlocked
→ 403

CallNotAllowed
→ 403

RateLimitExceeded
→ 429
```

Services should not need to raise raw `HTTPException`.

---

# 24. Pagination

Paginate all potentially growing collections.

Required for:

```text
friends
friend requests
matching results
conversations
messages
calls
admin user lists
reports
```

## Offset pagination

Acceptable for low-volume/admin lists:

```text
?limit=20&offset=0
```

## Cursor pagination

Preferred for:

```text
messages
conversation feeds
high-volume ordered histories
```

Example:

```text
?limit=50&before=message_cursor
```

MVP can start simple, but message APIs should be designed with cursor pagination in mind.

---

# 25. Filtering and Sorting

Use explicit query parameters.

Example:

```text
GET /admin/users?status=ACTIVE&limit=20
GET /matches?interest=Photography
GET /calls?status=ENDED
```

Avoid generic client-controlled SQL-like filters.

Only expose approved filters/sort fields.

---

# 26. Idempotency

Some operations should behave safely when retried.

Examples:

```text
accept friend request
cancel call
end call
logout
block user
```

If a repeated identical request represents the same final state, return a stable result rather than creating duplicate records.

For operations vulnerable to duplicate client retries, consider an idempotency key later.

Do not introduce a generic idempotency framework until needed.

---

# 27. Rate Limiting

Rate limiting is required for abuse-sensitive endpoints.

High priority:

```text
POST /auth/register
POST /auth/login
POST /auth/resend-otp
POST /auth/verify-email
POST /friends/requests
POST /reports
POST /calls
```

Redis is the intended rate-limit backend.

Policies belong in Security Architecture.

API behavior on limit:

```text
429 Too Many Requests
```

Optionally expose `Retry-After`.

---

# 28. File / Profile Image API

Do not send large binary image payloads through application database models.

Recommended patterns:

### Simple MVP

```text
Client
  ↓ multipart upload
FastAPI
  ↓
Storage adapter
  ↓
Object storage
```

### Later optimization

Use presigned upload URLs if supported by the selected storage provider.

Database stores only:

```text
object key / URL / metadata
```

Object storage stores the file.

---

# 29. API Security Rules

Never expose:

- password hashes
- OTPs/OTP hashes
- refresh-token hashes/raw records
- secret keys
- internal moderation notes to normal users
- SMTP/configuration details
- database IDs that are not appropriate for public exposure if a safer public ID is introduced

Validate:

- resource ownership
- role
- block relationship
- account status
- call/message eligibility

on every sensitive operation.

---

# 30. WebSocket Boundary

REST and WebSocket must share application services where business logic overlaps.

Example:

```text
REST POST /calls
                             → Call Application Service
              /
WS call.start
```

Do not implement one set of call rules in REST and a second copy inside WebSocket handlers.

WebSocket event design belongs in `REALTIME_ARCHITECTURE.md`.

---

# 31. Health and Readiness Endpoints

Recommended:

```text
GET /health/live
GET /health/ready
```

### Liveness

Answers:

```text
Is the process alive?
```

### Readiness

Answers:

```text
Can the application serve traffic?
```

Readiness should perform meaningful checks against required infrastructure according to production policy.

Avoid hardcoded:

```json
{
  "database": "connected",
  "redis": "connected"
}
```

without actual checks.

---

# 32. API Documentation

FastAPI OpenAPI/Swagger should remain enabled appropriately.

Recommended:

```text
/docs
/redoc
/openapi.json
```

For production, decide whether public documentation is:

- enabled
- restricted
- disabled

according to deployment/security needs.

Every production endpoint should have:

- clear summary
- request schema
- response schema
- documented expected errors where useful

---

# 33. API Compatibility

Once frontend depends on an endpoint, avoid unnecessary breaking changes.

Breaking changes include:

```text
renaming response fields
changing data types
changing URL structure
changing semantics
removing fields
```

When breaking changes become necessary:

```text
/api/v2
```

may be introduced.

Do not introduce v2 merely for internal refactoring when the public contract remains unchanged.

---

# 34. API Testing

Each feature should include API-level integration tests.

Examples:

## Auth

```text
register success
duplicate registration
invalid OTP
expired OTP
login success
login failure
refresh
logout
protected endpoint
```

## Profile

```text
get own profile
update own profile
view another authenticated user's profile
unauthenticated profile access denied
```

## Friendship

```text
send request
accept request
reject request
friend limit
blocked user
```

## Messaging

```text
conversation access
unauthorized conversation access
message pagination
retention behavior
```

## Calls

```text
start call eligibility
blocked call
offline/unavailable target
accept/reject/end authorization
```

## Admin

```text
regular user denied
admin succeeds
audit-sensitive actions
```

Use a real PostgreSQL test environment for integration tests where DB behavior matters.

---

# 35. Current API Cleanup Plan

From the current audit, address these before expanding the API heavily:

1. Remove/protect `/user_data`.
2. Remove/protect `DELETE /users/{user_id}` from Auth.
3. Normalize snake_case paths to kebab-case or resource conventions.
4. Move hardcoded `/api/v1/ping` into the API router/health structure.
5. Standardize destructive-operation status codes.
6. Introduce consistent error responses.
7. Keep Pydantic schemas separate from ORM models.
8. Move authentication dependencies to API transport dependencies.
9. Add pagination before user/match/message list endpoints grow.

---

# 36. Proposed MVP API Surface Summary

```text
AUTH
POST /api/v1/auth/register
POST /api/v1/auth/verify-email
POST /api/v1/auth/resend-otp
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/logout-all
GET  /api/v1/auth/me

PROFILE
GET   /api/v1/profiles/me
PATCH /api/v1/profiles/me
GET   /api/v1/profiles/{user_id}

LANGUAGE
GET /api/v1/languages
PUT /api/v1/profiles/me/languages

MATCHING
GET /api/v1/matches

FRIENDSHIP
GET    /api/v1/friends
POST   /api/v1/friends/requests
GET    /api/v1/friends/requests
POST   /api/v1/friends/requests/{id}/accept
POST   /api/v1/friends/requests/{id}/reject
DELETE /api/v1/friends/{user_id}
POST   /api/v1/friends/blocks
DELETE /api/v1/friends/blocks/{user_id}

MESSAGING
GET /api/v1/conversations
GET /api/v1/conversations/{id}
GET /api/v1/conversations/{id}/messages

CALLS
POST /api/v1/calls
GET  /api/v1/calls
GET  /api/v1/calls/{id}
POST /api/v1/calls/{id}/accept
POST /api/v1/calls/{id}/reject
POST /api/v1/calls/{id}/cancel
POST /api/v1/calls/{id}/end
POST /api/v1/calls/{id}/feedback

REPORTING
POST /api/v1/reports

ADMIN
GET  /api/v1/admin/users
GET  /api/v1/admin/users/{id}
POST /api/v1/admin/users/{id}/suspend
POST /api/v1/admin/users/{id}/activate
GET  /api/v1/admin/reports
POST /api/v1/admin/reports/{id}/resolve
```

This is a planning catalog, not an instruction to implement all endpoints immediately.

---

# 37. Implementation Order

Do not implement the entire API surface at once.

Recommended sequence:

```text
1. Clean/harden Auth API
2. Profile API
3. Language/Profile-language API
4. Matching API
5. Friendship/Block API
6. Realtime/WebSocket foundation
7. Messaging retrieval APIs + realtime send
8. Voice-call REST + signaling APIs/events
9. Feedback/reporting
10. Admin API
11. MVP hardening
```

---

# 38. Open API Decisions

Still to finalize:

1. Exact public-profile response fields.
2. Whether Profile update uses PUT, PATCH, or both.
3. User-language endpoint ownership.
4. Exact matching filters exposed publicly.
5. Exact friend-request route naming.
6. Whether direct conversations are explicitly created or lazily created on first interaction.
7. Whether REST message send fallback is required.
8. Call creation via REST vs exclusively realtime event.
9. Exact call-feedback response visibility.
10. Admin MVP endpoint scope.
11. Pagination cursor encoding.
12. Public resource IDs vs internal numeric IDs.
13. Exact error code catalog.

---

# 39. Next Architecture Artifact

```text
REQUIREMENTS_BASELINE.md       ✅
DOMAIN_BOUNDARIES.md           ✅
COMPONENT_ARCHITECTURE.md      ✅
DATABASE_ARCHITECTURE.md       ✅
API_ARCHITECTURE.md            ✅
        ↓
SECURITY_ARCHITECTURE.md       ← NEXT
        ↓
REALTIME_ARCHITECTURE.md
        ↓
TARGET_ARCHITECTURE.md
        ↓
ADR/*
        ↓
Application Workflows
        ↓
Feature Dependency Map
        ↓
Development Roadmap
        ↓
Epics / Stories / Tasks
        ↓
Jira
```
