# TalkTribe Component Architecture

**Status:** Stage 2 architecture design  
**Architecture style:** Modular Monolith  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `DOMAIN_BOUNDARIES.md`  
**Important scope correction:** Peer-to-peer **voice calling is an MVP capability**. Video calling remains future scope.

---

## 1. Purpose

This document defines how the major TalkTribe backend components fit together inside the modular monolith.

It focuses on:

- runtime component responsibilities
- dependency direction
- API/application/domain/infrastructure separation
- cross-domain communication
- transaction ownership
- repository boundaries
- dependency injection
- PostgreSQL, Redis, WebSocket, and external-service usage
- placement of peer-to-peer voice-call functionality
- how the existing Auth module fits into the target architecture

This document does **not** define the final database schema or full API catalog. Those belong in later architecture documents.

---

## 2. High-Level System View

```text
                        ┌──────────────────────┐
                        │    React Frontend    │
                        └──────────┬───────────┘
                                   │
                        REST / WebSocket / WebRTC
                                   │
                                   ▼
                     ┌─────────────────────────┐
                     │       FastAPI App       │
                     │  API + WS Transport     │
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │   Application Layer     │
                     │   Use-case orchestration│
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │      Domain Layer       │
                     │ Rules + contracts       │
                     └────────────┬────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              PostgreSQL        Redis       External
                                            Services
                                            Email
                                            Storage
                                            TURN/STUN
```

TalkTribe remains a **single deployable backend** for MVP.

The modules are logically separated, not deployed as microservices.

---

## 3. Target Backend Structure

Recommended target direction:

```text
backend/
└── app/
    ├── main.py
    │
    ├── api/
    │   ├── dependencies.py
    │   ├── errors.py
    │   └── router.py
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
    ├── shared/
    │   ├── exceptions.py
    │   ├── pagination.py
    │   └── types.py
    │
    └── realtime/
        ├── websocket/
        └── signaling/
```

The exact file names can change. The architectural responsibility is more important than the folder name.

---

## 4. Layer Responsibilities Inside a Domain

Each business domain follows four main layers.

```text
API
 ↓
Application
 ↓
Domain
 ↑
Infrastructure
```

### 4.1 API Layer

Responsible for transport concerns:

- FastAPI routes
- request parsing
- response schemas
- authentication dependency integration
- HTTP/WebSocket status mapping
- calling one application use case

The API layer should be thin.

Example:

```text
POST /api/v1/friends/requests
        ↓
Friendship API route
        ↓
SendFriendRequest use case
```

The route should not:

- build SQLAlchemy queries
- calculate business rules
- commit transactions
- call multiple repositories directly

---

## 5. Application Layer

The application layer coordinates complete business operations.

Examples:

```text
RegisterUser
VerifyRegistrationOtp
LoginUser
UpdateProfile
DiscoverMatches
SendFriendRequest
SendMessage
StartVoiceCall
EndVoiceCall
SuspendUser
```

Application services/use cases are responsible for:

- orchestration
- authorization/business permission checks
- transaction boundaries
- calling domain logic
- coordinating repositories/contracts
- invoking infrastructure ports

Example:

```text
RegisterUser
   │
   ├── validate account rules
   ├── create user
   ├── create OTP
   ├── save changes
   └── request email delivery
```

The complete database operation should be atomic where required.

---

## 6. Domain Layer

The domain layer owns business meaning and business rules.

Examples:

```text
Maximum friends = 20
Blocked users cannot interact
Only eligible candidates can be matched
Matching score is rule-based in MVP
Profile must satisfy completion rules
Call cannot start when target user is unavailable
```

The domain layer should avoid direct dependencies on:

- FastAPI
- SQLAlchemy sessions
- Redis clients
- SMTP
- HTTP clients
- WebRTC provider SDKs

The domain layer may define interfaces/contracts that infrastructure implements.

---

## 7. Infrastructure Layer

Infrastructure handles technical implementation details.

Examples:

```text
PostgreSQL
Redis
SMTP
Object storage
JWT cryptography
STUN/TURN configuration
Logging
Monitoring
```

Infrastructure implements ports/interfaces required by application/domain code.

Example:

```text
Application
    ↓
EmailSender interface
    ↓
SMTPEmailSender
```

A domain should depend on the interface, not the concrete provider.

---

# 8. Core MVP Components

## 8.1 Authentication Component

### Responsibilities

- registration
- OTP generation/verification
- login
- JWT access token
- refresh token lifecycle
- logout
- authenticated identity resolution
- password-reset flow when implemented

### Internal flow

```text
Auth API
   ↓
Auth Application
   ↓
Auth Domain
   ↓
Auth Repositories
   ↓
PostgreSQL
```

External dependency:

```text
Auth Application
      ↓
EmailSender
      ↓
SMTP adapter
```

### Existing implementation

The existing Auth module should be migrated/refined, not rewritten blindly.

Current working behavior should be preserved while:

- route orchestration is moved into application use cases
- repository boundaries are clarified
- transaction handling is centralized
- duplicate config/database/security infrastructure is removed
- authentication dependencies are moved to API/shared transport concerns

---

## 8.2 Profile Component

### Responsibilities

- profile creation
- profile update
- profile viewing
- profile picture metadata
- bio
- profession
- location
- interests
- visibility rules

### Depends on

```text
Authenticated identity
Language data
Storage adapter for image upload
```

### Flow

```text
Profile API
   ↓
Profile Application
   ↓
Profile Domain
   ↓
Profile Repository
   ↓
PostgreSQL
```

Profile must never expose password, OTP, refresh token, or secret authentication state.

---

## 8.3 Language Component

### Responsibilities

- supported language definitions
- English-first MVP support
- CEFR level validation: A1, A2, B1, B2, C1, C2
- user-language relationships if finalized as Language-owned data

### Notes

The component may remain lightweight in MVP.

It exists primarily so future language expansion does not require redesigning Profile or Matching.

---

## 8.4 Matching Component

### Responsibilities

- candidate selection
- eligibility filtering
- rule-based compatibility scoring
- returning up to 20 matches
- explaining recommendation reason where required

### Inputs

Matching consumes published information from:

```text
Profile
Language
Friendship/Block status
Availability/Presence where required
```

### Dependency rule

Allowed:

```text
Matching Application
   ↓
ProfileQuery contract
```

Forbidden:

```text
Matching
   ↓
ProfileRepository
```

### Flow

```text
GET /matches
      ↓
Matching Application
      ↓
Load eligible profile summaries
      ↓
Apply language/interests rules
      ↓
Exclude blocked/ineligible users
      ↓
Calculate compatibility
      ↓
Return <= 20 candidates
```

MVP matching remains rule-based.

AI matching is future.

---

## 8.5 Friendship / Connection Component

### Responsibilities

- friend request
- accept
- reject
- cancel
- remove
- friend list
- max-friend rule
- block/unblock
- interaction-eligibility contract

### Important rule

Maximum friends:

```text
20
```

### Exposes

Other components should ask Friendship:

```text
Can user A interact with user B?
Are they blocked?
Are they friends?
```

Other modules must not directly inspect Friendship tables.

---

## 8.6 Messaging Component

### Responsibilities

- conversations
- messages
- message history
- delivery/read state
- typing semantics
- conversation access
- one-week retention rule

### Runtime dependencies

```text
Messaging
   ├── PostgreSQL → durable messages
   ├── Redis → realtime distribution
   ├── Friendship contract → interaction permission
   └── Presence contract → online state when needed
```

### Message flow

```text
Client A
   ↓ WebSocket
Realtime Transport
   ↓
Messaging Application
   ↓
Authorize interaction
   ↓
Persist message
   ↓
Publish realtime event
   ↓
Redis Pub/Sub
   ↓
Client B connection
```

PostgreSQL remains the source of truth for durable messages.

Redis is not message history storage.

---

## 8.7 Presence Component

### Responsibilities

- online/offline state
- connection presence
- multiple device/session state
- heartbeat/expiry semantics
- realtime presence events

### Runtime store

Redis is the primary operational store for presence.

Example conceptual keys:

```text
presence:user:{user_id}
connections:user:{user_id}
```

Exact Redis key conventions belong in `REALTIME_ARCHITECTURE.md`.

---

## 8.8 Voice Call / Peer Connection Component

**MVP component.**

Voice calling is a core TalkTribe capability.

Video remains future.

### Responsibilities

- initiate voice call
- accept/reject call
- call-state lifecycle
- call eligibility
- signaling coordination
- call start/end state
- call history/statistics where required
- communication with presence/friendship rules

### Important separation

The backend does **not** carry the voice media stream.

For peer-to-peer voice:

```text
User A browser
       │
       │ WebRTC audio
       ▼
User B browser
```

The backend provides signaling/control:

```text
User A
   ↓
WebSocket signaling
   ↓
TalkTribe Backend
   ↓
WebSocket signaling
   ↓
User B
```

STUN/TURN assists WebRTC connectivity.

### Component flow

```text
Call API / signaling event
        ↓
Call Application
        ↓
Check authentication
        ↓
Check block/interaction rules
        ↓
Check presence/availability
        ↓
Create call state
        ↓
Exchange signaling events
        ↓
WebRTC peer connection
```

### Dependencies

```text
Calls
  ├── Friendship contract
  ├── Presence contract
  ├── Profile/identity summary
  ├── Redis for transient call/signaling coordination
  └── PostgreSQL if durable call history is required
```

### Must not

- put WebRTC signaling business rules directly in generic WebSocket handlers
- make Redis the durable call-history database
- let the frontend bypass backend authorization when initiating calls

---

## 8.9 Admin Component

### Responsibilities

- privileged user-management use cases
- moderation
- suspension/blocking at platform level
- administrative queries
- audit activity where required

### Dependency rule

Admin should orchestrate explicit contracts:

```text
Admin
   ↓
UserManagement contract
```

not:

```text
Admin
   ↓
UserRepository
FriendshipRepository
MessageRepository
...
```

Admin must not become a god module.

---

# 9. Cross-Domain Contracts

Cross-domain interaction should happen through small explicit contracts.

Examples:

```text
ProfileReader
FriendshipEligibility
PresenceReader
UserIdentityReader
LanguageReader
CallEligibility
```

These contracts should expose only the minimum required information.

Example:

```python
class FriendshipEligibility(Protocol):
    async def can_interact(self, user_id: int, peer_id: int) -> bool:
        ...
```

The exact Python interface style can be implemented with:

- `Protocol`
- abstract base classes
- application facade/service contracts

Do not over-engineer this initially.

Use the simplest style that preserves the boundary.

---

# 10. Dependency Injection

Dependencies should be assembled near the application boundary.

Conceptually:

```text
FastAPI dependency/container
        ↓
Application Service
        ├── Repository
        ├── Domain contract
        ├── Redis adapter
        └── External service adapter
```

Example:

```text
MatchingService
   ├── ProfileReader
   ├── FriendshipEligibility
   └── LanguageReader
```

Avoid constructing infrastructure dependencies inside domain logic.

---

# 11. Repository Architecture

Each repository belongs to the module that owns the data.

Example:

```text
domains/
├── auth/infrastructure/
│   ├── user_repository.py
│   ├── otp_repository.py
│   └── refresh_token_repository.py
│
├── profile/infrastructure/
│   └── profile_repository.py
│
├── friendship/infrastructure/
│   └── friendship_repository.py
│
└── messaging/infrastructure/
    ├── conversation_repository.py
    └── message_repository.py
```

Repositories:

- translate between persistence and application/domain needs
- contain SQLAlchemy query logic
- do not own high-level business rules

Services should not scatter raw SQLAlchemy queries across modules.

---

# 12. Transaction Architecture

Transactions should represent a complete business operation.

### Registration

Target:

```text
BEGIN
  create user
  create OTP
COMMIT

after commit / resilient delivery:
  send OTP email
```

The email delivery policy may use an outbox/background pattern later if reliability requires it.

### Send message

```text
BEGIN
  validate conversation
  persist message
COMMIT

publish realtime event
```

### Friend acceptance

```text
BEGIN
  verify request
  verify friend limit
  accept relationship
COMMIT
```

### Rule

Repositories should normally `flush`/persist through the active transaction, not make arbitrary independent commits.

The application/use-case boundary owns commit/rollback.

---

# 13. PostgreSQL Component

PostgreSQL is the primary durable data store.

It holds business records such as:

- authentication/account records
- profiles
- language relationships
- interests
- friendship/block records
- conversations
- messages
- call history if retained
- admin/audit records if required

PostgreSQL should enforce important integrity rules using:

- foreign keys
- unique constraints
- check constraints where useful
- indexes
- transactions

Exact schema belongs in `DATABASE_ARCHITECTURE.md`.

---

# 14. Redis Component

Redis is transient infrastructure.

Approved roles:

- WebSocket Pub/Sub
- presence
- rate limiting
- short-lived cache
- call/signaling coordination
- temporary realtime state
- coordination between backend instances

Not approved:

- primary user database
- durable message history
- durable friendship state
- durable call-history system of record

---

# 15. WebSocket Component

WebSocket is transport infrastructure.

It handles:

- connection establishment
- authenticated socket identity
- receive/send events
- connection registry
- heartbeat
- event serialization
- dispatch to application services

Example:

```text
Incoming event:
message.send
      ↓
WebSocket handler
      ↓
Messaging application
```

or:

```text
Incoming event:
call.offer
      ↓
WebSocket handler
      ↓
Call application/signaling service
```

The generic WebSocket handler must not contain Messaging or Call business rules.

---

# 16. WebRTC / Voice Architecture

Voice-call media uses WebRTC.

Backend responsibilities:

- authenticate signaling participants
- verify call eligibility
- coordinate call states
- exchange offer/answer/ICE signaling
- support STUN/TURN configuration
- optionally record call metadata

Frontend/browser responsibilities:

- microphone access
- WebRTC peer connection
- codec/media negotiation
- sending/receiving audio stream

Conceptual flow:

```text
User A
  │
  │ 1. request call
  ▼
Backend Call Service
  │
  │ 2. notify User B
  ▼
User B
  │
  │ 3. accept
  ▼
Backend signaling
  │
  ├── offer
  ├── answer
  └── ICE candidates
  │
  ▼
WebRTC peer connection
User A ⇄ User B
```

TURN is needed as a fallback when direct peer-to-peer connectivity fails.

Exact signaling protocol belongs in `REALTIME_ARCHITECTURE.md`.

---

# 17. Background Work

MVP should remain simple.

Potential background work:

- OTP/email delivery
- cleanup of expired OTPs/tokens
- message-retention cleanup
- future notifications
- analytics
- media processing if later required

Initially:

- FastAPI/background execution may be acceptable for non-critical lightweight work.

Later, introduce a dedicated job queue only when reliability/load requires it.

Do not introduce Celery/RabbitMQ/Kafka merely because background jobs exist.

---

# 18. Error Boundary

Domain/application layers should use application/domain exceptions.

Example:

```text
FriendLimitReached
UserBlocked
ProfileIncomplete
CallNotAllowed
InvalidOtp
```

The API layer maps those to HTTP responses.

```text
Domain/Application error
       ↓
API exception handler
       ↓
HTTP response
```

This avoids importing `HTTPException` throughout business services.

---

# 19. Authentication vs Authorization

Authentication:

```text
Who is the caller?
```

Authorization:

```text
May this caller perform this action?
```

Transport layer resolves authenticated identity.

Application services enforce action-specific authorization.

Example:

```text
GET /profiles/{id}
    ↓
authenticated identity
    ↓
Profile application service
    ↓
Can this authenticated user view the profile?
    ↓
return safe profile
```

---

# 20. Current Auth Migration Strategy

Because authentication already works, migrate it incrementally.

Recommended sequence:

```text
1. Add tests around existing behavior
2. Consolidate configuration
3. Consolidate database/session infrastructure
4. Consolidate password/JWT security utilities
5. Move API authentication dependencies out of business services
6. Introduce User/Otp/RefreshToken repositories consistently
7. Move registration orchestration into one application use case
8. Fix transaction ownership
9. Harden OTP/rate limiting
10. Preserve endpoint behavior while refactoring internals
```

Do not rewrite the entire module at once.

---

# 21. Component Dependency Matrix

| Component | Auth | Profile | Language | Friendship | Presence | Redis | PostgreSQL |
|---|---|---|---|---|---|---|---|
| Auth | — | No | No | No | No | optional/rate-limit | Yes |
| Profile | Identity | — | Yes | No | No | cache optional | Yes |
| Language | Identity/ref | related | — | No | No | optional | Yes |
| Matching | Identity | Read contract | Read contract | Eligibility contract | optional | cache optional | own persistence only if needed |
| Friendship | Identity | User summary | No | — | optional | optional | Yes |
| Messaging | Identity | minimal summary | No | Eligibility contract | Read contract | Pub/Sub | Yes |
| Presence | Identity | No | No | No | — | Yes | generally No |
| Calls | Identity | summary | No | Eligibility | Required | signaling/state | call history if needed |
| Admin | Role/Auth | contracts | contracts | contracts | contracts | optional | only via owned/approved access |

“Read contract” does not mean importing that domain's repository.

---

# 22. Frontend Component Direction

Frontend should also evolve toward feature ownership.

Recommended direction:

```text
src/
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

A feature may contain:

```text
auth/
├── components/
├── hooks/
├── api/
├── store/
└── types/
```

Avoid a future situation where all API calls live in one giant `services/` folder and all state in one giant `store/`.

---

# 23. What Must Be Changed Before Next Major Feature

Before implementing Profile/Matching/Calls aggressively:

## Change now

1. Protect/remove insecure user-list/delete endpoints.
2. Consolidate configuration.
3. Consolidate database/session infrastructure.
4. Establish automated auth tests.
5. Fix transaction ownership in authentication.
6. Establish canonical security/JWT utilities.
7. Finalize the Auth module's application/repository boundary.
8. Define authentication and authorization dependencies cleanly.

## Can be introduced with the relevant feature

1. Redis application client.
2. Presence implementation.
3. WebSocket connection manager.
4. Call signaling service.
5. TURN/STUN production setup.
6. Matching cache.
7. Dedicated background job queue.

---

# 24. What Should Not Be Added Yet

Avoid premature complexity:

- microservices
- Kubernetes
- Kafka
- event sourcing
- complex CQRS
- separate databases per domain
- AI matching
- video-call media architecture
- notification infrastructure
- practice-session architecture
- distributed job systems unless genuinely required

---

# 25. Architecture Invariants

The following rules should remain true as TalkTribe grows:

1. One deployable backend for MVP.
2. Business modules have explicit owners.
3. Cross-domain repository imports are prohibited.
4. API/WebSocket transport remains thin.
5. Application services coordinate use cases and transactions.
6. Domain logic is infrastructure-independent where practical.
7. PostgreSQL stores durable business truth.
8. Redis handles transient/distributed realtime state.
9. WebRTC carries voice media; backend coordinates signaling and authorization.
10. Admin does not bypass architecture boundaries.
11. New infrastructure is introduced only for a concrete requirement.
12. Tests protect existing behavior during architecture migration.

---

# 26. Remaining Architecture Documents

After this document:

```text
COMPONENT_ARCHITECTURE.md       ✅
        ↓
DATABASE_ARCHITECTURE.md        ← NEXT
        ↓
API_ARCHITECTURE.md
        ↓
SECURITY_ARCHITECTURE.md
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

---

## 27. Required Follow-up Correction

`DOMAIN_BOUNDARIES.md` should be amended so that:

```text
Voice Call / Peer Connection
```

is an **MVP domain**, while:

```text
Video calling
```

remains future scope.

This correction keeps the architecture aligned with the product requirement that voice connection is the core TalkTribe experience.
