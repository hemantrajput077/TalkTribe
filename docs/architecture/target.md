# TalkTribe Target Architecture

**Status:** Stage 2 target architecture baseline  
**Architecture style:** Modular Monolith  
**Backend:** FastAPI  
**Frontend:** React  
**Primary database:** PostgreSQL  
**Transient/realtime store:** Redis  
**Realtime transport:** WebSocket  
**Voice media:** WebRTC  
**Deployment target:** Low-cost MVP deployment with a path to scale later

**Depends on:**
- `REQUIREMENTS_BASELINE.md`
- `DOMAIN_BOUNDARIES.md`
- `COMPONENT_ARCHITECTURE.md`
- `DATABASE_ARCHITECTURE.md`
- `API_ARCHITECTURE.md`
- `SECURITY_ARCHITECTURE.md`
- `REALTIME_ARCHITECTURE.md`

---

# 1. Purpose

This document consolidates the target architecture for TalkTribe.

It describes:

- the overall system architecture
- backend module boundaries
- frontend feature boundaries
- API architecture
- database architecture
- Redis responsibilities
- realtime communication
- automatic co-learner pairing
- voice calling
- authentication and authorization
- admin boundaries
- external-service integration
- deployment shape
- testing and observability direction
- migration from the current implementation
- implementation order

This is the main architecture reference for future feature design and implementation.

---

# 2. Product Architecture Summary

TalkTribe is a language-practice platform where an authenticated learner can:

```text
Register
   ↓
Verify account
   ↓
Login
   ↓
Complete profile
   ↓
Set language/interests
   ↓
Become available
   ↓
Find / get paired with compatible co-learner
   ↓
Connect
   ↓
Talk through voice
   ↓
Chat / interact
   ↓
Rate or report
   ↓
Repeat
```

The architecture must support this core journey without requiring microservices or unnecessary distributed complexity.

---

# 3. Architecture Style

TalkTribe will use a:

```text
MODULAR MONOLITH
```

This means:

- one backend application
- one primary deployment unit
- one PostgreSQL database
- one Redis service
- clearly separated business modules
- explicit dependency rules
- no direct cross-domain repository access

This is not a microservice architecture.

---

# 4. Why Modular Monolith

The current project is early-stage and initially targets a small user base.

A modular monolith provides:

- simpler deployment
- lower infrastructure cost
- easier local development
- easier debugging
- easier transactions
- clear business boundaries
- good testability
- future extraction path if one domain needs independent scaling

Microservices are explicitly deferred until there is a concrete scaling or organizational reason.

---

# 5. High-Level Architecture

```text
                           ┌────────────────────┐
                           │   React Frontend   │
                           └─────────┬──────────┘
                                     │
                        REST / WebSocket / WebRTC
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │   FastAPI Backend    │
                         │   Modular Monolith   │
                         └─────────┬────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
  Business Domains          Shared Infrastructure       Realtime Transport
        │                          │                          │
        │                          │                          │
        ▼                          ▼                          ▼
   Application Layer      PostgreSQL / Redis / Email      WebSocket
        │                                                   Signaling
        ▼
   Domain Rules
        │
        ▼
   Repositories
```

---

# 6. Target Backend Structure

Recommended target structure:

```text
backend/
└── app/
    ├── main.py
    │
    ├── api/
    │   ├── router.py
    │   ├── dependencies.py
    │   └── errors.py
    │
    ├── domains/
    │   ├── auth/
    │   │   ├── api/
    │   │   ├── application/
    │   │   ├── domain/
    │   │   ├── infrastructure/
    │   │   └── schemas/
    │   │
    │   ├── profile/
    │   ├── language/
    │   ├── matching/
    │   ├── friendship/
    │   ├── messaging/
    │   ├── presence/
    │   ├── calls/
    │   └── admin/
    │
    ├── infrastructure/
    │   ├── config/
    │   ├── database/
    │   ├── redis/
    │   ├── email/
    │   ├── storage/
    │   ├── security/
    │   └── observability/
    │
    ├── realtime/
    │   ├── websocket/
    │   └── signaling/
    │
    └── shared/
        ├── exceptions.py
        ├── pagination.py
        └── types.py
```

Not every folder should be created immediately.

Create a domain folder when that domain is actually being implemented.

---

# 7. Target Frontend Structure

Recommended direction:

```text
frontend/src/
├── app/
│   ├── router/
│   └── providers/
│
├── features/
│   ├── auth/
│   ├── profile/
│   ├── matching/
│   ├── friendship/
│   ├── chat/
│   ├── calls/
│   └── admin/
│
├── shared/
│   ├── components/
│   ├── hooks/
│   ├── api/
│   ├── types/
│   └── utils/
│
└── pages/
```

Each feature should own:

```text
components
hooks
API calls
state
types
feature-specific utilities
```

Avoid placing all frontend API logic into one giant `services/` directory.

---

# 8. Domain Map

MVP domains:

```text
Auth
Profile
Language
Matching
Friendship / Connection
Messaging
Presence
Calls / Peer Connection
Admin
```

Future domains:

```text
Notifications
Practice Sessions
Video Calling
Communities
Gamification
AI Matching
AI Tutor
Analytics
```

---

# 9. Domain Responsibilities

## Auth

Owns:

```text
registration
OTP verification
login
JWT
refresh tokens
logout
account verification
authentication identity
```

## Profile

Owns:

```text
profile data
bio
profession
location
profile photo
interests
profile visibility
```

## Language

Owns:

```text
language reference data
proficiency levels
user-language relationships
```

## Matching

Owns:

```text
candidate filtering
compatibility rules
ranking
top 20 recommendations
```

## Friendship

Owns:

```text
friend request
accept/reject
friend removal
friend limit
blocking
interaction eligibility
```

## Messaging

Owns:

```text
conversations
messages
delivery state
read state
typing semantics
message retention
```

## Presence

Owns:

```text
online/offline state
connection presence
multi-device presence
```

## Calls

Owns:

```text
automatic pairing
manual friend calls
call lifecycle
call eligibility
WebRTC signaling coordination
call history
```

## Admin

Owns:

```text
user moderation
privileged operations
report handling
admin audit
```

---

# 10. Dependency Direction

Inside a domain:

```text
API
 ↓
Application
 ↓
Domain
 ↑
Infrastructure
```

Meaning:

- API depends on Application
- Application uses Domain rules
- Infrastructure implements repository/service contracts
- Domain should not depend on FastAPI, Redis, SMTP, or SQLAlchemy-specific behavior

---

# 11. Cross-Domain Communication

A domain must not directly access another domain's repository.

Allowed:

```text
Messaging
   ↓
FriendshipEligibility contract
```

Forbidden:

```text
Messaging
   ↓
FriendshipRepository
```

Allowed:

```text
Matching
   ↓
ProfileReader contract
```

Forbidden:

```text
Matching
   ↓
ProfileRepository
```

Cross-domain interaction happens through:

```text
application services
published interfaces/contracts
query services
facades
```

---

# 12. API Architecture

All production APIs are versioned under:

```text
/api/v1
```

Top-level domain API groups:

```text
/api/v1/auth
/api/v1/profiles
/api/v1/languages
/api/v1/matches
/api/v1/friends
/api/v1/conversations
/api/v1/calls
/api/v1/reports
/api/v1/admin
```

Routes remain thin.

They should handle:

```text
request parsing
authentication dependency
schema validation
application service call
HTTP response mapping
```

Business logic stays outside routes.

---

# 13. Authentication Architecture

Authentication flow:

```text
Register
   ↓
Create account
   ↓
Generate OTP
   ↓
Send email
   ↓
Verify OTP
   ↓
Activate account
   ↓
Login
   ↓
Access + Refresh Token
```

Security requirements:

- password hashing
- hashed OTP storage
- OTP expiry
- OTP retry limits
- resend cooldown
- short-lived access tokens
- refresh-token rotation
- refresh-token revocation
- logout-all
- rate limiting

---

# 14. Authorization Architecture

Authentication answers:

```text
Who is the user?
```

Authorization answers:

```text
Can the user perform this action?
```

Roles:

```text
USER
ADMIN
```

Authorization is enforced:

1. at API/transport boundary
2. inside application services

Examples:

```text
Can current user edit this profile?
Can current user message this peer?
Can current user call this peer?
Can current user view this conversation?
Can current user perform admin action?
```

---

# 15. Profile Visibility

Final decision:

```text
Unauthenticated user → cannot view profiles
Authenticated learner → can view permitted co-learner profile
Admin → can view according to admin policy
```

Normal users must never receive:

```text
password hash
email unless explicitly allowed
phone number
OTP data
refresh-token data
security flags
admin moderation notes
```

---

# 16. PostgreSQL Architecture

PostgreSQL is the durable business database.

Target table groups:

```text
Auth
├── users
├── otps
└── refresh_tokens

Profile
├── profiles
├── interests
└── user_interests

Language
├── languages
└── user_languages

Friendship
├── friend_requests
├── friendships
└── user_blocks

Messaging
├── conversations
├── conversation_participants
└── messages

Calls
├── voice_calls
└── call_feedback

Admin
├── user_reports
└── admin_audit_logs
```

Tables should be added only with the feature that needs them.

---

# 17. Database Ownership

Each domain owns its data.

Example:

```text
Messaging owns messages.
Friendship owns friendships.
Profile owns profile records.
```

Another module may read necessary information through a contract.

It must not directly modify foreign-domain tables.

---

# 18. Transaction Architecture

Transactions are owned by complete application use cases.

Example registration:

```text
BEGIN
  create user
  create OTP
COMMIT

send email
```

Example friend acceptance:

```text
BEGIN
  validate pending request
  validate block state
  validate friend limit
  create friendship
  mark request accepted
COMMIT
```

Repositories should not commit independently.

---

# 19. Redis Architecture

Redis is used for transient/distributed state.

Approved responsibilities:

```text
presence
WebSocket Pub/Sub
rate limiting
pairing queue
temporary call state
realtime coordination
short-lived cache
```

Redis is not used as:

```text
primary user database
message history database
friendship database
call-history database
```

---

# 20. Realtime Architecture

WebSocket is the realtime transport.

It handles:

```text
presence
chat events
typing
read receipts
pairing events
incoming calls
call state
WebRTC signaling
```

WebSocket handlers remain transport-only.

Business rules are delegated to:

```text
Messaging Application
Presence Application
Calls Application
Matching Application
Friendship Application
```

---

# 21. Presence Architecture

Presence is primarily stored in Redis.

Rule:

```text
user online
=
at least one active WebSocket connection
```

Multi-device support is required.

A heartbeat/TTL mechanism removes stale connections.

PostgreSQL is not the live presence store.

---

# 22. Automatic Co-Learner Pairing

Automatic pairing is a core TalkTribe MVP capability.

Flow:

```text
User joins pairing
   ↓
Validate profile/account
   ↓
Add to Redis waiting pool
   ↓
Find compatible available user
   ↓
Apply Matching rules
   ↓
Exclude blocked/ineligible users
   ↓
Atomically reserve both users
   ↓
Create call state
   ↓
Notify both users
   ↓
Begin WebRTC signaling
```

Matching and Pairing are separate:

```text
Matching = who is compatible?
Pairing = who is available now?
```

---

# 23. Matching Architecture

MVP matching is rule-based.

Inputs may include:

```text
English language compatibility
proficiency
interests
hobbies
profession
block/eligibility state
availability where relevant
```

Return:

```text
up to 20 candidate suggestions
```

AI/embedding matching is future work.

---

# 24. Voice Call Architecture

Voice is a core MVP capability.

Video is future.

Voice media uses WebRTC.

Backend handles:

```text
authentication
authorization
call eligibility
call lifecycle
signaling
offer/answer relay
ICE candidate relay
STUN/TURN configuration support
call metadata
```

Frontend handles:

```text
microphone
WebRTC peer connection
audio tracks
media state
```

Normal media flow:

```text
User A ⇄ WebRTC ⇄ User B
```

The backend is not the primary media relay.

---

# 25. STUN / TURN

Connectivity strategy:

```text
WebRTC direct P2P
      ↓
STUN-assisted connectivity
      ↓
TURN fallback if direct connection fails
```

TURN is important for reliable production calling.

Provider choice remains an infrastructure decision.

---

# 26. Messaging Architecture

Durable messages are persisted before realtime acknowledgement.

Flow:

```text
Client A
   ↓ WebSocket
Messaging Application
   ↓
authorize
   ↓
persist PostgreSQL
   ↓
commit
   ↓
publish Redis event
   ↓
Client B
```

If B is offline:

```text
message remains in PostgreSQL
```

On reconnect, B retrieves recent/unread messages.

---

# 27. Message Retention

Current business rule:

```text
message history retained for 1 week
```

A background cleanup job should enforce this.

Redis Pub/Sub is never used as durable message storage.

---

# 28. Friendship and Blocking

Friendship limit:

```text
maximum 20 friends
```

Blocking affects:

```text
friend requests
matching
messages
voice calls
other peer interaction
```

Existing conversation history remains, but new communication is blocked.

---

# 29. Admin Architecture

Admin is part of MVP.

Admin is a privileged application/domain module, not a shortcut around boundaries.

Admin may perform approved operations through domain contracts.

Example:

```text
Admin
   ↓
UserManagement contract
```

not:

```text
Admin
   ↓
direct modification of every repository
```

Sensitive admin actions should be audited.

---

# 30. Reports and Feedback

After a call, user may:

```text
rate co-learner
report co-learner
```

Rating contributes to future profile/statistics.

Reports feed Admin moderation.

Potential data:

```text
call_feedback
user_reports
admin_audit_logs
```

---

# 31. External Services

External services are accessed through adapters.

Examples:

```text
EmailSender
StorageService
TURN credential provider
future NotificationService
```

Business domains should not directly depend on provider SDKs.

Example:

```text
Auth
  ↓
EmailSender interface
  ↓
SMTP adapter
```

---

# 32. Background Work

Possible asynchronous/background tasks:

```text
email sending
expired OTP cleanup
expired refresh-token cleanup
message retention cleanup
analytics
future notifications
```

Start simple.

Use FastAPI/background execution or a simple worker when sufficient.

Do not introduce Kafka/Celery/RabbitMQ without a real need.

---

# 33. Error Architecture

Business/application exceptions:

```text
InvalidOtp
FriendLimitReached
UserBlocked
CallNotAllowed
ProfileIncomplete
```

API maps them into consistent HTTP responses.

Realtime maps them into consistent WebSocket error events.

Business services should not depend directly on `HTTPException`.

---

# 34. Testing Architecture

Testing layers:

```text
Unit tests
Application/service tests
Repository integration tests
API integration tests
WebSocket tests
Security/authorization tests
Realtime/call tests
```

Use real PostgreSQL for important integration behavior.

Redis may use a test Redis instance or suitable isolated test strategy.

Critical existing Auth behavior should be protected with tests before substantial refactoring.

---

# 35. Observability

Initial production observability should include:

```text
structured logs
request IDs
error logs
health checks
basic metrics
```

Useful realtime metrics later:

```text
active users
active WebSockets
pairing queue size
pairing success rate
active calls
call connection failures
message delivery latency
```

---

# 36. Health Architecture

Recommended:

```text
/health/live
/health/ready
```

Liveness:

```text
process running?
```

Readiness:

```text
can service handle required traffic?
```

Readiness should perform real infrastructure checks where appropriate.

Avoid hardcoded “connected” values.

---

# 37. Deployment Architecture

Initial low-cost target:

```text
Frontend
→ Vercel

Backend
→ AWS EC2
→ Docker
→ Nginx
→ FastAPI

Database
→ Supabase / Neon PostgreSQL initially

Redis
→ Redis Cloud initially

Images
→ Supabase Storage / Cloudflare R2

HTTPS
→ Let's Encrypt / Cloudflare

CI/CD
→ GitHub Actions
```

This is one practical MVP deployment direction, not a permanent architecture lock.

---

# 38. Deployment Diagram

```text
                     Internet
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
          Vercel              AWS EC2
         Frontend               Nginx
              │                   │
              └──── HTTPS/WSS ────┤
                                  ▼
                              FastAPI
                         ┌────────┼────────┐
                         │        │        │
                         ▼        ▼        ▼
                    PostgreSQL  Redis   External
                                       Services
```

For voice:

```text
User A ⇄ WebRTC/STUN/TURN ⇄ User B
```

---

# 39. CI/CD Architecture

Recommended pipeline:

```text
Git Push / PR
      ↓
GitHub Actions
      ↓
Lint
      ↓
Type Check
      ↓
Security Scan
      ↓
Tests
      ↓
Build
      ↓
Deploy
```

Possible tools already present:

```text
ruff
mypy
bandit
pytest
```

Alembic migration validation should be added to CI when database workflows mature.

---

# 40. Current-to-Target Migration Strategy

Do not rewrite the application.

Move incrementally.

## Step 1 — Stabilize Auth

- add tests
- remove insecure endpoints
- consolidate config
- consolidate database/session setup
- consolidate security utilities
- fix JWT secret configuration
- hash OTP
- fix transaction boundaries
- add rate limiting

## Step 2 — Finalize Auth module boundaries

- thin routes
- application use cases
- repositories
- infrastructure adapters
- API auth dependency location

## Step 3 — Build Profile

Use the new target architecture from day one.

## Step 4 — Build Language

Add language/proficiency data.

## Step 5 — Build Matching

Rule-based recommendations.

## Step 6 — Build Friendship / Blocking

Required before unrestricted peer interaction.

## Step 7 — Build Redis + Realtime foundation

- Redis client
- WebSocket auth
- connection manager
- presence
- Pub/Sub

## Step 8 — Build Pairing + Voice Calls

- pairing queue
- call lifecycle
- signaling
- WebRTC
- STUN/TURN

## Step 9 — Build Messaging

- durable messages
- realtime delivery
- read receipts
- typing

## Step 10 — Feedback / Reporting / Admin

- ratings
- reports
- moderation
- admin audit

## Step 11 — MVP Hardening

- tests
- security
- monitoring
- CI/CD
- deployment
- performance review

---

# 41. Feature Dependency Direction

Recommended dependency flow:

```text
Auth
 ↓
Profile
 ↓
Language
 ↓
Matching
 ↓
Friendship / Blocking
 ↓
Realtime Foundation
 ↓
Automatic Pairing
 ↓
Voice Calls
 ↓
Messaging
 ↓
Feedback / Reports
 ↓
Admin
 ↓
MVP Hardening
```

Some features can be developed partially in parallel, but this is the logical dependency order.

---

# 42. Architecture Invariants

The following rules should remain true:

1. TalkTribe is one deployable backend for MVP.
2. Modules are organized by business capability.
3. Cross-domain repository access is forbidden.
4. Routes stay thin.
5. Application layer owns orchestration and transactions.
6. Domain rules remain independent of transport/infrastructure where practical.
7. PostgreSQL stores durable truth.
8. Redis stores transient/distributed realtime state.
9. WebSocket is transport, not business logic.
10. WebRTC carries voice media.
11. Backend controls call authorization/signaling.
12. Admin does not bypass module boundaries.
13. Infrastructure is introduced only for real requirements.
14. Existing working Auth behavior is protected during refactor.
15. Tests are part of feature completion.

---

# 43. Architecture Decisions Requiring ADRs

The following should become ADRs:

```text
ADR-001 Modular Monolith
ADR-002 Domain-Oriented Backend Structure
ADR-003 PostgreSQL as Primary Durable Store
ADR-004 Redis for Realtime/Presence/PubSub
ADR-005 WebSocket for Realtime Transport
ADR-006 WebRTC for Voice Calls
ADR-007 Backend Signaling, P2P Media
ADR-008 Application-Level Transaction Ownership
ADR-009 Cross-Domain Communication Through Contracts
ADR-010 JWT + Refresh Token Authentication
ADR-011 Admin as MVP Role
ADR-012 Rule-Based Matching for MVP
ADR-013 One-Week Message Retention
ADR-014 Notifications Deferred Until After P2P
```

Each ADR should contain:

```text
Context
Decision
Alternatives
Consequences
Status
```

---

# 44. Open Architecture Decisions

Still open:

1. Exact Auth vs Profile data split for `full_name`.
2. Exact user-language cardinality rules.
3. Exact interest ownership/moderation behavior.
4. Exact account-status values.
5. Exact profile fields visible to authenticated users.
6. Exact messaging permission preference model.
7. Exact call eligibility rules.
8. Exact pairing timeout and ranking tie-breaker.
9. Exact WebSocket handshake authentication method.
10. Presence heartbeat/TTL.
11. TURN provider.
12. Exact Admin MVP operation list.
13. Account deletion vs audit/report retention.
14. Exact backup RPO/RTO.
15. Exact NFR latency/SLA targets.
16. Exact ordering of Messaging vs Voice implementation if team capacity changes.

These do not block the architecture baseline as long as they remain explicitly tracked.

---

# 45. Architecture Stage Completion

Stage 2 architecture artifacts:

```text
REQUIREMENTS_BASELINE.md       ✅
DOMAIN_BOUNDARIES.md           ✅
COMPONENT_ARCHITECTURE.md      ✅
DATABASE_ARCHITECTURE.md       ✅
API_ARCHITECTURE.md            ✅
SECURITY_ARCHITECTURE.md       ✅
REALTIME_ARCHITECTURE.md       ✅
TARGET_ARCHITECTURE.md         ✅
```

Remaining Stage 2 work:

```text
ADR/*
```

After ADRs are created, proceed to Stage 3:

```text
Application Workflows
```

---

# 46. Next Project Phase

After architecture decisions are recorded:

```text
TARGET ARCHITECTURE
        ↓
ADRs
        ↓
WORKFLOWS
        ↓
FEATURE DEPENDENCY MAP
        ↓
DEVELOPMENT ROADMAP
        ↓
EPICS
        ↓
STORIES
        ↓
TASKS
        ↓
ACCEPTANCE CRITERIA
        ↓
JIRA
        ↓
IMPLEMENTATION
```

---

# 47. Final Target Architecture Diagram

```text
                                  ┌──────────────────────┐
                                  │    React Frontend    │
                                  └──────────┬───────────┘
                                             │
                              REST / WebSocket / WebRTC
                                             │
                                             ▼
                               ┌────────────────────────┐
                               │     FastAPI Backend    │
                               │    Modular Monolith    │
                               └────────────┬───────────┘
                                            │
       ┌────────────────────────────────────┼────────────────────────────────────┐
       │                                    │                                    │
       ▼                                    ▼                                    ▼
 ┌─────────────┐                      ┌─────────────┐                       ┌─────────────┐
 │ Auth        │                      │ Profile     │                       │ Admin       │
 ├─────────────┤                      ├─────────────┤                       ├─────────────┤
 │ Matching    │                      │ Friendship  │                       │ Reports     │
 ├─────────────┤                      ├─────────────┤                       └─────────────┘
 │ Messaging   │                      │ Presence    │
 ├─────────────┤                      ├─────────────┤
 │ Calls       │                      │ Language    │
 └──────┬──────┘                      └──────┬──────┘
        │                                    │
        └──────────────────┬─────────────────┘
                           │
                           ▼
              ┌───────────────────────────────┐
              │       Application Layer       │
              │ Use Cases / Authorization     │
              │ Transactions / Contracts      │
              └──────────────┬────────────────┘
                             │
              ┌──────────────┼───────────────┐
              │              │               │
              ▼              ▼               ▼
         PostgreSQL        Redis         External Services
       durable business   presence       email / storage
           data           Pub/Sub        STUN / TURN
                          pairing
                          cache
                          limits

Voice media path:
User A  ⇄  WebRTC / STUN / TURN  ⇄  User B
```
