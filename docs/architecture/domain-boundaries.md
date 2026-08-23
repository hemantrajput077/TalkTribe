# TalkTribe Domain Boundaries

**Status:** Stage 2 architecture baseline  
**Architecture style:** Modular Monolith  
**Scope:** MVP domain ownership, responsibilities, dependencies, and prohibited coupling

## 1. Purpose

This document defines the business-module boundaries for TalkTribe. It answers:

- Which module owns each business capability?
- What may a module expose?
- What may it depend on?
- What data may it modify?
- What cross-module access is prohibited?

The goal is to keep TalkTribe maintainable as Profile, Matching, Friendship, Messaging, Presence, and Admin are added.

## 2. Core Boundary Rules

1. Organize backend business code by domain/capability.
2. A domain owns its business rules and domain-specific persistence.
3. A module must not directly use another module's repository or modify another module's tables.
4. Cross-domain operations go through explicit application contracts/services.
5. FastAPI, SQLAlchemy, Redis, SMTP, and other infrastructure details must not become core domain rules.
6. API/WebSocket code is transport code; it should delegate business decisions to application/domain code.
7. PostgreSQL is the durable system of record.
8. Redis stores/distributes transient or derived state such as presence, Pub/Sub, cache, and rate-limit state.
9. Transactions are owned by application/use-case boundaries.
10. Future domains must not be implemented prematurely merely because a folder can be created.

## 3. MVP Domain Map

```text
Identity/Auth
User/Profile
Language
Matching
Friendship/Connection
Messaging
Presence
Admin
```

Future domains:

```text
Notifications
Practice Sessions
Voice/Video
Communities
Gamification
AI-assisted Matching
```

## 4. Identity / Authentication

### Owns
- Registration
- Account verification
- OTP lifecycle
- Login
- Password authentication
- Access-token creation
- Refresh-token lifecycle
- Logout/authentication revocation rules
- Authentication identity/security state

### Exposes
- Register account
- Verify account/OTP
- Authenticate credentials
- Refresh authentication
- Logout/revoke session
- Resolve authenticated identity through an application/API contract

### Depends on
- Database infrastructure
- Security/cryptographic infrastructure
- Email interface/adapter
- Configuration
- Clock/time abstraction where useful

### May read
- Authentication-owned user identity/account state required to authenticate.

### May modify
- Authentication/account security data
- OTP records
- Refresh-token/session records

### Must not
- Own profile business rules
- Implement matching/friendship/chat rules
- Directly modify another domain's persistence
- Contain FastAPI-specific behavior in its core domain layer
- Directly depend on SMTP/provider-specific behavior in business logic

## 5. User / Profile

### Owns
- User-facing profile
- Bio
- Profession
- Location
- Profile-photo metadata/reference
- Profile completion/update rules
- Profile visibility rules that are intrinsic to profile access

### Exposes
- Get own profile
- Get viewable profile
- Create/complete profile
- Update own profile
- Provide safe profile summaries to other modules

### Depends on
- Auth identity contract for current authenticated identity
- Storage interface if profile images require external object storage
- Language contract/data as finalized in database design

### May read
- Authentication identity identifier/status needed to associate a profile
- Language/profile-related reference data

### May modify
- Profile-owned records only

### Must not
- Issue JWTs
- Directly query Auth repositories
- Decide matching scores
- Modify friendship/message records
- Expose sensitive authentication fields through profile responses

## 6. Language

**Boundary status:** Candidate lightweight domain/reference-data module. Final independence is confirmed during database/component design.

### Owns
- Supported language master data
- CEFR proficiency definitions/rules where represented in the application
- User-language relationships if we choose Language as their owner

### Exposes
- List supported languages
- Validate supported language/proficiency
- Provide user language-learning information through a contract

### Depends on
- Database infrastructure
- User identity/profile association as required by final model

### Must not
- Own matching scoring
- Own user authentication
- Directly modify profile, friendship, or messaging data

### Note
MVP initially supports English, but the model should allow additional languages without a fundamental redesign.

## 7. Matching / Discovery

### Owns
- Candidate discovery
- Candidate eligibility rules specific to matching
- Rule-based compatibility calculation
- Ranking
- Returning up to 20 suggestions

### Exposes
- Discover matches for an authenticated user
- Calculate/return compatibility information where product requirements allow

### Depends on
- Profile summary contract
- Language information contract
- Friendship/block eligibility contract

### May read
Only the minimum cross-domain data exposed through contracts needed to build candidates and scores.

### May modify
Preferably no other domain's data. Matching-specific persistence may be introduced only if a real requirement requires it.

### Must not
- Directly query User/Profile repositories
- Directly query Friendship repositories
- Change profile/friendship records
- Introduce embedding/AI matching in MVP

## 8. Friendship / Connection

### Owns
- Connection/friend requests
- Request lifecycle
- Accepted relationships
- Friend removal
- Maximum-friend rule (currently 20)
- Blocking relationship/state
- Connection eligibility rules

### Exposes
- Send request
- Accept/reject/cancel request
- Remove connection
- List relationships
- Block/unblock where supported
- Query whether two users may interact according to relationship/block state

### Depends on
- Authenticated identity
- Minimal user existence/status contract

### May modify
- Friendship/request/block-owned records

### Must not
- Directly edit profiles
- Persist chat messages
- Determine authentication
- Directly access another module's repository

## 9. Messaging

### Owns
- Conversations
- Messages
- Message persistence
- Delivery/read state semantics
- Typing-event business semantics where required
- Conversation access rules
- One-week message-history retention requirement

### Exposes
- Create/access eligible conversation
- Send message
- Retrieve permitted message history
- Mark/read delivery state
- Process messaging events

### Depends on
- Authenticated identity
- Friendship/Block interaction-eligibility contract
- Presence contract for transient online-state decisions where required
- Realtime transport/infrastructure

### May modify
- Conversation/message-owned records

### Must not
- Own WebSocket connection implementation as business logic
- Directly query Friendship repositories
- Treat Redis as durable message storage
- Modify profile/authentication data

## 10. Presence

### Owns
- Online/offline semantics
- User connection presence
- Multi-session/device presence rules
- Presence expiry/reconnection behavior

### Exposes
- Mark session online/offline
- Query presence
- Publish/consume presence changes as required

### Depends on
- Authenticated identity
- Redis infrastructure
- WebSocket connection lifecycle

### Persistence
Presence is primarily transient state. Redis is the intended operational store/distribution mechanism; PostgreSQL should not become the primary presence store unless a future durable requirement appears.

### Must not
- Persist chat history
- Own authentication
- Decide friendship rules
- Become a generic dumping ground for all WebSocket behavior

## 11. Admin

### Owns
- Administrative use cases
- Moderation orchestration
- Privileged user-management actions
- Admin-specific authorization policies/use cases
- Administrative audit requirements when finalized

### Exposes
- MVP admin operations that are explicitly approved

### Depends on
- Authentication/role information
- Contracts exposed by domains on which an administrative action operates

### Important rule
Admin is not allowed to bypass every boundary by importing every repository. It should orchestrate privileged operations through explicit domain/application contracts wherever practical.

### Must not
- Become a shared `god module`
- Contain ordinary user/profile/messaging business logic simply because an admin can act on it

## 12. Infrastructure

Infrastructure is not a business domain.

```text
infrastructure/
├── config/
├── database/
├── cache/       # Redis client/infrastructure
├── email/
├── security/
└── observability/   # when introduced
```

It owns technical adapters and shared runtime facilities.

Infrastructure may implement interfaces required by application/domain code, but business rules should not be moved into infrastructure.

## 13. API Layer

The API layer owns HTTP transport concerns:

- Route registration
- Request/response mapping
- FastAPI dependencies
- Authentication extraction
- API versioning
- HTTP status/error translation

It must remain thin.

```text
HTTP
 ↓
API
 ↓
Application use case
 ↓
Domain rules
 ↓
Repository/interface
```

The API layer must not become the main location for business orchestration.

## 14. WebSocket Layer

WebSocket is a transport boundary, not a business domain.

It owns:
- Connection acceptance/lifecycle
- Transport authentication integration
- Event parsing/serialization
- Connection routing
- Passing events to Messaging/Presence application services

It must not own:
- message authorization rules
- friendship rules
- message persistence rules
- presence business semantics

## 15. Shared Package

`shared/` must stay intentionally small.

Allowed examples:
- generic application exceptions
- common immutable primitives/value objects with genuine cross-domain meaning
- generic pagination types
- common typing/protocol utilities

Not allowed:
- random helpers
- domain-specific services
- repositories shared merely for convenience
- a generic `utils.py` dumping ground

Rule: if code clearly belongs to one domain, keep it in that domain.

## 16. Allowed Dependency Direction

Conceptually:

```text
API / WebSocket Transport
          ↓
Application / Use Cases
          ↓
Domain Rules + Contracts
          ↑
Infrastructure Adapters
```

Cross-domain:

```text
Domain A application service
          ↓
Published contract/interface of Domain B
          ↓
Domain B application service
```

Forbidden:

```text
Matching → FriendshipRepository
Messaging → UserRepository
Admin → every repository
Domain → FastAPI
Domain → Redis client
Domain → SMTP client
```

## 17. Data Ownership Baseline

| Data | Primary Owner |
|---|---|
| Authentication identity/account security state | Auth |
| OTP | Auth |
| Refresh token/session | Auth |
| User profile | User/Profile |
| Language master data | Language |
| User language/proficiency | Language or Profile — finalize in DB design |
| Interests | Profile or dedicated reference data — finalize in DB design |
| Friend request | Friendship |
| Friendship | Friendship |
| Block relationship | Friendship |
| Conversation | Messaging |
| Message | Messaging |
| Presence | Presence/Redis |
| Admin audit record | Admin — if required |

No module may update another module's owned table merely because the database is shared.

## 18. High-Level Domain Dependencies

```text
                     Auth
                      │
          authenticated identity
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   User/Profile    Friendship      Admin
        │             │
        ├──────┐      │ interaction eligibility
        │      │      ▼
        │   Language  Messaging
        │      │         │
        └──┬───┘         │
           ▼             ▼
        Matching       Presence
```

This diagram expresses conceptual dependencies, not direct repository imports.

## 19. Future Domains

The following remain outside MVP architecture implementation:

### Notifications
Introduced after peer-to-peer connection/realtime work. It should consume relevant application/domain events rather than forcing Messaging/Friendship to own notification delivery.

### Practice Sessions
Future scheduling/session capability.

### Voice/Video
Future realtime media capability; WebRTC or provider choices are not an MVP architecture requirement.

### AI Matching
Future enhancement to the Matching domain. MVP matching remains rule-based.

## 20. Boundary Enforcement Checklist

Before merging a feature, verify:

- [ ] The owning domain is clear.
- [ ] Business logic is not in the route/controller.
- [ ] The domain does not import FastAPI/Redis/SMTP unnecessarily.
- [ ] Cross-domain access uses an explicit contract/application interface.
- [ ] No foreign domain repository is imported.
- [ ] Only the owning module modifies its data.
- [ ] Transaction ownership is explicit.
- [ ] Authorization is checked at the application/use-case boundary.
- [ ] Tests cover important business and authorization rules.
- [ ] New shared code genuinely belongs in `shared/`.
- [ ] Architecture documentation/ADR is updated if a boundary changed.

## 21. Open Decisions for Following Documents

The following are intentionally deferred to the next architecture artifacts:

1. Whether user-language relationships are owned by Profile or Language.
2. Exact interest ownership/data model.
3. Exact Auth/User identity table separation.
4. Cross-domain contract implementation style in Python.
5. Unit-of-work/transaction implementation.
6. Exact admin MVP operations.
7. Messaging permission matrix.
8. Block behavior for existing conversations.
9. Message delivery/read/reconnect semantics.
10. Exact Redis key/event conventions.
11. API response/error conventions.
12. Database tables, keys, indexes, and constraints.

## 22. Approval Gate

This document should be approved before creating detailed database/API/realtime designs.

Once approved, proceed to:

```text
COMPONENT_ARCHITECTURE.md
        ↓
DATABASE_ARCHITECTURE.md
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
