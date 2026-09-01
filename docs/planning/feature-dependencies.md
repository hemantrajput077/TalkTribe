# TalkTribe Feature Dependencies

**Stage:** 4 — Feature Decomposition / Planning  
**Status:** Dependency baseline  
**Purpose:** Define implementation order, prerequisite relationships, parallel work, and critical path for TalkTribe MVP.

**Depends on:**
- `REQUIREMENTS_BASELINE.md`
- `TARGET_ARCHITECTURE.md`
- `AUTHENTICATION_WORKFLOW.md`
- `PROFILE_WORKFLOW.md`
- `LANGUAGE_WORKFLOW.md`
- `MATCHING_WORKFLOW.md`
- `FRIENDSHIP_WORKFLOW.md`
- `PRESENCE_WORKFLOW.md`
- `PAIRING_WORKFLOW.md`
- `VOICE_CALL_WORKFLOW.md`
- `MESSAGING_WORKFLOW.md`
- `FEEDBACK_REPORTING_WORKFLOW.md`
- `ADMIN_WORKFLOW.md`

---

# 1. Purpose

This document defines the dependency order between TalkTribe MVP features.

It answers:

- Which feature must be completed first?
- Which feature depends on another?
- Which features can be developed in parallel?
- Which features are on the critical path to the core TalkTribe experience?
- Which infrastructure must exist before realtime communication?
- Which work can be deferred without blocking the MVP?
- What implementation order should be used when generating epics, stories, and Jira tickets?

This is not a Jira backlog.

It is the planning layer that should come **before** backlog generation.

---

# 2. Core Product Goal

The critical TalkTribe user journey is:

```text
Register
   ↓
Verify
   ↓
Login
   ↓
Complete Profile
   ↓
Configure Language / Interests
   ↓
Find Compatible Learner
   ↓
Become Available
   ↓
Get Paired
   ↓
Voice Call
   ↓
Rate / Report
   ↓
Talk Again
```

Therefore the implementation dependency graph must protect this journey.

---

# 3. Dependency Levels

Features are grouped into levels.

```text
Level 0 → Engineering foundation
Level 1 → Identity foundation
Level 2 → User/profile foundation
Level 3 → Social/compatibility foundation
Level 4 → Realtime foundation
Level 5 → Core connection experience
Level 6 → Communication extensions
Level 7 → Trust/moderation
Level 8 → Production hardening
```

A later level may begin partially before every earlier feature is 100% polished, but its hard dependencies must be stable.

---

# 4. High-Level Dependency Graph

```text
                    ENGINEERING FOUNDATION
                            │
                            ▼
                         AUTH
                            │
                            ▼
                         PROFILE
                            │
                            ▼
                        LANGUAGE
                            │
                    ┌───────┴────────┐
                    ▼                ▼
                 MATCHING        FRIENDSHIP
                    │                │
                    └───────┬────────┘
                            ▼
                  REALTIME FOUNDATION
                    │               │
                    ▼               ▼
                 PRESENCE       REDIS / WS
                    │               │
                    └───────┬───────┘
                            ▼
                         PAIRING
                            │
                            ▼
                       VOICE CALLS
                            │
                    ┌───────┴────────┐
                    ▼                ▼
                MESSAGING      FEEDBACK/REPORTING
                                     │
                                     ▼
                                   ADMIN
                                     │
                                     ▼
                              MVP HARDENING
```

---

# 5. Level 0 — Engineering Foundation

Before building additional business features, the project needs a stable engineering baseline.

## Required foundation

```text
Configuration
Database/session infrastructure
Alembic migration workflow
Canonical security utilities
Test infrastructure
Linting/type checking
CI baseline
Environment management
Error handling conventions
```

## Existing direction

Current tooling already includes:

```text
FastAPI
SQLAlchemy
Alembic
pytest
pytest-asyncio
httpx
ruff
mypy
bandit
Docker
```

The exact CI implementation should be verified from the repository before claiming it complete.

---

# 6. Foundation Work That Blocks Other Features

The following should be fixed before major feature expansion:

```text
duplicate configuration
duplicate database/session setup
duplicate password/security utilities
JWT secret inconsistency
insecure user-list/delete endpoints
transaction-boundary issues
lack of sufficient automated Auth protection
```

These are not separate product features, but they are implementation prerequisites.

---

# 7. Level 1 — Authentication

## Feature

```text
Authentication / Identity
```

## Depends on

```text
Engineering Foundation
PostgreSQL
Email adapter
Security utilities
```

## Provides

```text
AuthenticatedIdentity
USER / ADMIN role
verified-account state
active-account state
JWT access token
refresh-token lifecycle
```

## Required by

```text
Profile
Language
Matching
Friendship
Messaging
Presence
Pairing
Voice Calls
Feedback/Reporting
Admin
```

Authentication is the most important hard dependency in the system.

---

# 8. Auth Stabilization Gate

Before Profile implementation should depend heavily on Auth, Auth should satisfy:

```text
registration works
verification works
login works
refresh works
logout works
protected identity works
critical security issues fixed
tests protect existing behavior
```

Not every future auth feature must be finished first.

For example:

```text
Google login
advanced account recovery
MFA
```

do not block Profile.

---

# 9. Level 2 — Profile

## Feature

```text
User Profile
```

## Hard dependencies

```text
Auth
PostgreSQL
Storage abstraction for profile photo when implemented
```

## Provides

```text
profile data
profile completion status
safe public profile summary
interests
profession/location
profile eligibility
```

## Required by

```text
Language setup
Matching
Friendship presentation
Pairing eligibility
Call UI
Feedback profile display
Admin moderation context
```

---

# 10. Profile Can Start Before Photo Upload

Profile-photo storage is not a hard dependency for the rest of Profile because photo is optional.

Recommended:

```text
Profile core fields
        ↓
Profile completion
        ↓
Matching/Pairing

Photo upload can be completed in parallel
```

This keeps optional media infrastructure from blocking the critical path.

---

# 11. Level 2 — Language

## Feature

```text
Language / Proficiency
```

## Hard dependencies

```text
Auth
Profile setup workflow
PostgreSQL
```

## Provides

```text
English-practice eligibility
mother tongue
spoken languages
A1–C2 proficiency
language summary
```

## Required by

```text
Profile completion
Matching
Pairing
Call partner context
```

Language is logically separate but can be implemented alongside Profile.

---

# 12. Profile and Language Parallelization

Recommended development:

```text
Profile core model/API
        │
        ├──────────────┐
        ▼              ▼
Interests          Language
        │              │
        └──────┬───────┘
               ▼
       Profile Completion
```

This allows some work in parallel.

---

# 13. Level 3 — Matching

## Feature

```text
Rule-Based Matching
```

## Hard dependencies

```text
Auth
Profile
Language
Block/interaction eligibility contract
```

## Soft dependencies

```text
Presence
Friendship status
```

Presence is not required for ordinary discovery.

Friendship status may enhance response state but is not required for compatibility itself.

## Provides

```text
candidate eligibility
compatibility score
ranked recommendations
max 20 candidates
matching compatibility service for Pairing
```

## Required by

```text
Discovery UI
Automatic Pairing
```

---

# 14. Matching and Friendship Dependency Nuance

Matching absolutely needs:

```text
block exclusion
```

However the entire friend-request UI does not need to be complete before the matching engine itself is coded.

Possible sequence:

```text
InteractionEligibility contract defined
        ↓
Matching implemented
        ↓
Friendship persistence/requests completed
```

But before production Matching is considered complete:

```text
block behavior must exist
```

because blocked users must never be recommended.

---

# 15. Level 3 — Friendship / Blocking

## Feature

```text
Friendship / Connection
```

## Hard dependencies

```text
Auth
Profile summary
PostgreSQL
```

## Provides

```text
friend requests
accepted friendships
20-friend limit
blocking
InteractionEligibility
```

## Required by

```text
Matching block exclusion
Manual friend calls
Messaging permission
Pairing exclusion
```

Blocking is more critical to downstream safety than the friend-list UI itself.

---

# 16. Friendship Internal Priority

Recommended order inside Friendship:

```text
1. Block model + eligibility
2. Friend request model
3. Send request
4. Accept/reject/cancel
5. Friend list
6. Friend removal
7. Max-20 concurrency hardening
```

Blocking and eligibility should be available before realtime communication.

---

# 17. Level 4 — Redis Foundation

Before realtime product features:

```text
Redis async client
connection configuration
health behavior
basic abstractions
```

must exist.

Redis is required by:

```text
Presence
WebSocket Pub/Sub
Pairing queue
Call availability
Rate limiting
```

Redis should not be introduced into domains directly.

---

# 18. Level 4 — Authenticated WebSocket Foundation

## Hard dependencies

```text
Auth
canonical JWT validation
realtime event conventions
```

## Provides

```text
authenticated socket
server-side user identity
connection lifecycle
event dispatcher
```

## Required by

```text
Presence
Pairing
Voice Calls
Realtime Messaging
```

This is a critical-path component.

---

# 19. Level 4 — Connection Manager

The Connection Manager depends on:

```text
Authenticated WebSocket
```

and provides:

```text
user → connection mapping
multiple tabs/devices
local event delivery
disconnect handling
```

Required by:

```text
Presence
Messaging
Call signaling
```

---

# 20. Level 4 — Presence

## Hard dependencies

```text
Auth
WebSocket Foundation
Connection Manager
Redis
```

## Provides

```text
online/offline state
connection availability
PresenceReader
```

## Required by

```text
Pairing
Manual friend calls
Realtime delivery optimization
Friends online indicator
```

Presence is a hard dependency for live pairing and voice calls.

---

# 21. Level 4 — Redis Pub/Sub

## Hard dependencies

```text
Redis
Realtime event envelope
```

## Provides

```text
cross-instance realtime event delivery
```

Required eventually by:

```text
Messaging
Presence updates
Pairing
Call signaling
```

At one backend instance, basic local delivery can work first.

However the architecture should introduce the abstraction before feature code assumes all users are local.

---

# 22. Level 5 — Pairing

## Feature

```text
Automatic Co-Learner Pairing
```

## Hard dependencies

```text
Auth
Profile completeness
Language eligibility
Matching compatibility
Blocking eligibility
Presence
Redis
Authenticated WebSocket
```

## Provides

```text
waiting queue
candidate selection
atomic reservation
paired-user result
call handoff
```

## Required by

```text
Automatic voice-call core experience
```

Pairing is one of the core critical-path features.

---

# 23. Pairing Must Not Wait for Messaging

Messaging is **not** a hard dependency for Pairing.

Core MVP can progress:

```text
Pairing
   ↓
Voice Call
```

without requiring chat to be completed first.

This is important because voice connection is the primary product goal.

---

# 24. Level 5 — Voice Calls

## Feature

```text
Peer-to-Peer Voice Calls
```

## Hard dependencies

```text
Auth
Presence
Friendship/Block eligibility
Pairing for automatic calls
WebSocket signaling
Redis call state
WebRTC frontend capability
STUN
```

For manual friend calls:

```text
Friendship
Presence
Calls
```

For automatic calls:

```text
Pairing
Calls
```

## Provides

```text
call lifecycle
signaling
voice connection
call history
post-call event
```

## Required by

```text
Feedback / Rating
Call-based Reports
Core TalkTribe value proposition
```

---

# 25. TURN Dependency

TURN is not strictly required to begin local/development WebRTC experiments.

But production-ready Voice Calls require a TURN fallback strategy.

Therefore:

```text
WebRTC local/dev call
        ↓
STUN
        ↓
TURN production hardening
```

TURN is a **release dependency**, not necessarily a first-code dependency.

---

# 26. Level 6 — Messaging

## Feature

```text
1:1 Messaging
```

## Hard dependencies

```text
Auth
Friendship/Block eligibility
PostgreSQL
Authenticated WebSocket
Connection Manager
```

## Useful dependency

```text
Presence
Redis Pub/Sub
```

## Provides

```text
direct conversation
message persistence
online/offline delivery
typing
read receipts
```

Messaging can be developed after realtime foundation and in parallel with some Call hardening.

---

# 27. Messaging vs Voice Priority

Product critical path:

```text
Voice Call > Messaging
```

because the core experience is speaking with a co-learner.

Recommended:

```text
Realtime Foundation
       ↓
Pairing
       ↓
Voice Call
       ↓
Messaging
```

If team capacity allows, Messaging persistence/API can be built in parallel with Voice frontend signaling work.

---

# 28. Level 7 — Feedback / Reporting

## Feature

```text
Feedback / Rating / Reporting
```

## Hard dependencies

Rating:

```text
Auth
Voice Call history
Profile target
```

Reporting:

```text
Auth
target user
Admin moderation model
optional Call/Conversation context
```

## Provides

```text
ratings
profile rating source
safety reports
admin moderation input
```

---

# 29. Reporting Can Partially Start Earlier

A generic profile report can technically exist before Voice Calls.

However the agreed user journey prioritizes:

```text
post-call report
```

Therefore full Feedback/Reporting should follow Call implementation.

---

# 30. Level 7 — Admin

## Feature

```text
Admin / Moderation
```

## Hard dependencies

```text
Auth roles
Security authorization
User/account state
Reports
```

## Provides

```text
admin user list
report review
suspend/reactivate
audit trail
```

Admin is MVP.

Some admin foundation can start earlier:

```text
ADMIN role
require_admin()
account status
```

while the full moderation interface waits for Reports.

---

# 31. Admin Split

Recommended split:

## Admin Foundation — early

```text
ADMIN role
admin authorization
account status
basic protected user management
```

## Admin Moderation — later

```text
report queue
resolve/dismiss
audit
moderation actions
```

This reduces blocking between Auth and later Reports.

---

# 32. Level 8 — MVP Hardening

After the core features work together:

```text
Security hardening
Performance review
Observability
CI/CD
Deployment
Backup verification
TURN production reliability
Rate limiting
Error consistency
Load/concurrency tests
Documentation
```

This is not optional before production release.

---

# 33. Critical Path

The shortest logical path to the core TalkTribe value is:

```text
Engineering Foundation
        ↓
Auth Stabilization
        ↓
Profile
        ↓
Language
        ↓
Matching
        ↓
Blocking / Eligibility
        ↓
Redis + WebSocket
        ↓
Presence
        ↓
Pairing
        ↓
Voice Calls
```

This is the **critical path**.

If a critical-path feature is delayed, the core MVP is delayed.

---

# 34. Core MVP Completion Path

After Voice Calls:

```text
Voice Calls
   ├── Messaging
   ├── Feedback / Reporting
   │        ↓
   │      Admin Moderation
   │
   └── Production Hardening
```

---

# 35. Parallel Work Opportunities

## After Auth stabilizes

Can partially run in parallel:

```text
Profile
Language reference-data groundwork
Admin-role foundation
```

## After Profile + Language

Can partially run in parallel:

```text
Matching
Friendship
```

## After WebSocket/Redis foundation

Can partially run in parallel:

```text
Presence
Messaging persistence/API
Call frontend WebRTC prototype
```

## After Voice Call lifecycle

Can run in parallel:

```text
Feedback
Reporting
Messaging hardening
Admin moderation UI/API
```

---

# 36. Work That Should NOT Block Core MVP

These are future/non-critical-path items:

```text
Notifications
Practice Sessions
Video Calls
Communities
Leaderboards
Streaks
Badges
Rewards
AI Matching
AI Tutor
Grammar Feedback
Pronunciation Scoring
Advanced Analytics
Google Login
Microservices
Kubernetes
Kafka
```

Do not allow them to delay core P2P voice functionality.

---

# 37. Feature Dependency Matrix

| Feature | Hard Dependencies | Provides To |
|---|---|---|
| Engineering Foundation | — | All backend features |
| Auth | Foundation | Every protected domain |
| Profile | Auth | Language, Matching, Pairing, Calls |
| Language | Auth, Profile | Matching, Pairing |
| Matching | Profile, Language, Block eligibility | Discovery, Pairing |
| Friendship/Blocking | Auth, Profile | Matching, Messaging, Pairing, Calls |
| Redis Foundation | Config/Infra | Presence, Pub/Sub, Pairing, Calls |
| WebSocket Foundation | Auth | Presence, Messaging, Pairing, Calls |
| Presence | Auth, WS, Redis | Pairing, Calls, Messaging |
| Pairing | Matching, Presence, Blocking, Redis | Automatic Calls |
| Voice Calls | Presence, WS, Pairing/Friendship, WebRTC | Feedback, core MVP |
| Messaging | Auth, Blocking, WS, PostgreSQL | Communication |
| Feedback/Reporting | Calls/User context | Profile rating, Admin |
| Admin | Auth roles, Reports | Moderation |
| Hardening | Integrated MVP | Production release |

---

# 38. Domain Contract Dependencies

Modules should depend on contracts, not repositories.

```text
Matching
  → ProfileMatchingReader
  → LanguageReader
  → InteractionEligibility

Messaging
  → InteractionEligibility
  → PresenceReader

Pairing
  → MatchingCompatibility
  → InteractionEligibility
  → PresenceReader
  → CallAvailability

Calls
  → InteractionEligibility
  → PresenceReader
  → ProfileSummaryReader

Admin
  → UserManagement
  → ReportManagement
```

---

# 39. Database Dependency Order

Recommended schema evolution:

```text
users
otps
refresh_tokens
        ↓
profiles
        ↓
languages
user_languages
interests
user_interests
        ↓
friend_requests
friendships
user_blocks
        ↓
conversations
conversation_participants
messages
        ↓
voice_calls
call_feedback
        ↓
user_reports
admin_audit_logs
```

Only create schema for the feature being implemented.

---

# 40. API Dependency Order

```text
Auth API
   ↓
Profile API
   ↓
Language API
   ↓
Matching API
   ↓
Friendship API
   ↓
WebSocket
   ↓
Pairing Events
   ↓
Call Events/API
   ↓
Messaging API/Events
   ↓
Feedback/Report API
   ↓
Admin API
```

---

# 41. Frontend Dependency Order

```text
Auth screens
   ↓
Profile setup
   ↓
Home / discovery
   ↓
Match cards
   ↓
Friend state
   ↓
Realtime provider / socket
   ↓
Online state
   ↓
Talk Now / pairing UI
   ↓
Call screen
   ↓
Chat
   ↓
Feedback/report UI
   ↓
Admin UI
```

---

# 42. Testing Dependency Order

Tests should be created with each feature.

Do not defer all testing until the end.

Recommended:

```text
Auth tests
   ↓
Profile tests
   ↓
Language tests
   ↓
Matching tests
   ↓
Friendship concurrency/security tests
   ↓
WebSocket/Presence tests
   ↓
Pairing concurrency tests
   ↓
Call signaling tests
   ↓
Messaging tests
   ↓
Admin/Report authorization tests
   ↓
End-to-end MVP journey
```

---

# 43. End-to-End Integration Test Dependency

The final core integration test should simulate:

```text
User A registers
User B registers
        ↓
both verify/login
        ↓
both complete profiles
        ↓
both configure English/proficiency/interests
        ↓
matching identifies compatibility
        ↓
both connect WebSocket
        ↓
both become online
        ↓
both join pairing
        ↓
system pairs A+B
        ↓
voice call established
        ↓
call ends
        ↓
A rates/reports if desired
```

This test proves the central TalkTribe journey works.

---

# 44. Definition of Ready for a Feature

Before implementation starts, a feature should have:

```text
clear owner/domain
approved workflow
known dependencies
API expectations
database impact
security rules
acceptance criteria
test expectations
```

If these are unknown, the story is not ready for implementation.

---

# 45. Definition of Complete Dependency

A dependency does **not** mean every possible sub-feature is finished.

Example:

Profile is ready for Matching when:

```text
safe summary exists
interests exist
language data exists
profile completion works
```

Profile-photo deletion polish does not need to block Matching.

Use the minimum stable contract required by the dependent feature.

---

# 46. Feature Slicing Principle

Avoid:

```text
"Build entire Profile domain"
```

before anything else can start.

Prefer vertical slices:

```text
Profile Core
   ↓
Profile Completion
   ↓
Profile Matching Contract
```

Then continue optional profile improvements in parallel.

---

# 47. Recommended Implementation Milestones

## Milestone A — Foundation + Auth

```text
engineering cleanup
auth stabilization
tests/security
```

## Milestone B — Learner Identity

```text
profile
language
interests
```

## Milestone C — Discovery + Safety

```text
matching
friendship
blocking
```

## Milestone D — Realtime Foundation

```text
Redis
WebSocket
ConnectionManager
presence
```

## Milestone E — Core Talk Experience

```text
pairing
voice call
STUN/TURN
```

## Milestone F — Communication

```text
messaging
read receipts
typing
```

## Milestone G — Trust + Moderation

```text
feedback
reports
admin
```

## Milestone H — Production Readiness

```text
CI/CD
security hardening
observability
deployment
backup
performance
```

---

# 48. Blocking Risks

The main dependency risks are:

## Auth instability

If Auth continues changing while every module integrates directly with it, downstream work becomes unstable.

Mitigation:

```text
stable AuthenticatedIdentity contract
```

## Cross-domain repository access

Creates hidden dependencies.

Mitigation:

```text
explicit contracts
```

## Realtime built before basic domain rules

Can create duplicated business logic in WebSocket handlers.

Mitigation:

```text
application services first
transport second
```

## Pairing before atomic reservation design

Can double-pair users.

Mitigation:

```text
Redis concurrency test before release
```

## Voice call before block/availability rules

Can allow unauthorized calls.

Mitigation:

```text
InteractionEligibility + PresenceReader
```

---

# 49. Change Management

When a new requirement appears:

```text
New Requirement
      ↓
Identify owning domain
      ↓
Check dependency graph
      ↓
Does it change existing dependency?
   ├── No → add to feature backlog
   └── Yes
        ↓
update architecture/workflow if needed
        ↓
add/supersede ADR if architectural
        ↓
update FEATURE_DEPENDENCIES.md
        ↓
create Jira work
```

Do not reorder implementation based only on Jira issue numbers.

---

# 50. MVP vs Future Dependency Separation

## MVP

```text
Auth
Profile
Language
Matching
Friendship/Blocking
Presence
Pairing
Voice Call
Messaging
Feedback/Reporting
Admin
Hardening
```

## Future

```text
Notifications
Practice Sessions
Video
Groups
Communities
Gamification
AI
```

Future dependencies should be designed later when those features become active planning scope.

---

# 51. Next Planning Artifact

With dependencies defined:

```text
Requirements                   ✅
Architecture                   ✅
Workflows                      ✅
FEATURE_DEPENDENCIES.md        ✅
        ↓
DEVELOPMENT_ROADMAP.md         ← NEXT
        ↓
FEATURE_CATALOG.md
        ↓
EPIC_CATALOG.md
        ↓
Stories
        ↓
Tasks
        ↓
Acceptance Criteria
        ↓
Jira
        ↓
Implementation
```

---

# 52. Final Dependency Diagram

```text
                           FOUNDATION
                               │
                               ▼
                              AUTH
                               │
                               ▼
                            PROFILE
                               │
                               ▼
                            LANGUAGE
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
                 MATCHING            FRIENDSHIP
                    │                 + BLOCKING
                    └──────────┬──────────┘
                               │
                               ▼
                     REALTIME FOUNDATION
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
                  REDIS    WEBSOCKET   PRESENCE
                    └──────────┼──────────┘
                               ▼
                            PAIRING
                               │
                               ▼
                         VOICE CALLS
                         /           \
                        ▼             ▼
                 MESSAGING      FEEDBACK/REPORTING
                                      │
                                      ▼
                                    ADMIN
                                      │
                                      ▼
                              MVP HARDENING
                                      │
                                      ▼
                              PRODUCTION MVP
```
