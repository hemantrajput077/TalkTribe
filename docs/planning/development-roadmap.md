# TalkTribe Development Roadmap

**Stage:** 4 — Feature Decomposition / Planning  
**Status:** Roadmap baseline  
**Architecture:** Modular Monolith  
**Purpose:** Convert approved requirements, architecture, workflows, and dependencies into an execution sequence for the TalkTribe MVP.

**Depends on:**
- `REQUIREMENTS_BASELINE.md`
- `TARGET_ARCHITECTURE.md`
- `FEATURE_DEPENDENCIES.md`
- Stage 3 workflow documents

---

# 1. Purpose

This document defines the implementation roadmap for TalkTribe.

It answers:

- What should be built first?
- What should be built next?
- Which milestones depend on earlier milestones?
- Which work can happen in parallel?
- What must be true before a milestone is considered complete?
- Which work belongs to MVP?
- Which work should be deferred?
- When should Jira epics/stories/tasks be generated?
- How should changes be introduced without breaking the plan?

This roadmap is intentionally dependency-driven rather than date-driven.

No artificial delivery dates are assigned here.

---

# 2. MVP Goal

The core TalkTribe MVP journey is:

```text
Register
   ↓
Verify Account
   ↓
Login
   ↓
Complete Profile
   ↓
Configure Language / Interests
   ↓
Discover Compatible Learners
   ↓
Become Online
   ↓
Join Pairing
   ↓
Connect to Co-Learner
   ↓
Voice Conversation
   ↓
Rate / Report
   ↓
Talk Again
```

Everything in the roadmap should support this journey.

---

# 3. Roadmap Principles

1. Build the critical path first.
2. Stabilize existing Auth before expanding heavily.
3. Create infrastructure only when a feature needs it.
4. Prefer vertical feature slices.
5. Do not create every table/folder/API in advance.
6. Tests are part of implementation, not a final phase.
7. Security and authorization are built into each feature.
8. Realtime transport must stay separate from business logic.
9. Voice connection is prioritized over optional messaging polish.
10. Future features must not delay MVP.

---

# 4. Roadmap Overview

```text
M0 — Engineering Baseline
        ↓
M1 — Authentication Stabilization
        ↓
M2 — Profile + Language Foundation
        ↓
M3 — Matching + Friendship/Blocking
        ↓
M4 — Realtime Foundation
        ↓
M5 — Automatic Pairing
        ↓
M6 — Voice Calling
        ↓
M7 — Messaging
        ↓
M8 — Feedback + Reporting
        ↓
M9 — Admin Moderation
        ↓
M10 — MVP Hardening + Deployment
        ↓
Production MVP
```

---

# 5. Milestone 0 — Engineering Baseline

## Goal

Create a stable foundation before more product features are added.

## Main work

```text
configuration cleanup
database/session cleanup
security utility cleanup
test infrastructure
API error conventions
CI baseline
code-quality tooling
environment handling
health-check cleanup
```

## Specific actions

### Backend structure

Confirm current modular structure:

```text
app/domains/
app/infrastructure/
app/shared/
app/realtime/
```

Do not restructure again unless a real architecture problem exists.

### Configuration

Consolidate to one canonical configuration system.

Required config areas:

```text
database
JWT
Redis
email
storage
CORS
environment
logging
```

### Database

Consolidate:

```text
engine
session factory
get_db dependency
transaction strategy
```

### Security utilities

Choose one canonical implementation for:

```text
password hashing
JWT encode/decode
token validation
```

Remove duplicate/dead implementations after tests protect behavior.

### Testing

Ensure:

```text
pytest
pytest-asyncio
httpx
test DB setup
```

are working.

Prefer real PostgreSQL for important integration tests.

### Code quality

Keep:

```text
ruff
mypy
bandit
```

as part of local/CI quality gates.

---

# 6. Milestone 0 Exit Criteria

Milestone 0 is complete when:

- [ ] One configuration system is authoritative.
- [ ] One DB/session implementation is authoritative.
- [ ] One password/JWT utility path is authoritative.
- [ ] Test suite can run locally.
- [ ] API startup is deterministic.
- [ ] No fake database/Redis health status remains.
- [ ] Critical lint/type/security checks can run.
- [ ] Existing Auth behavior is protected enough to refactor safely.

---

# 7. Milestone 1 — Authentication Stabilization

## Goal

Turn the existing working Auth implementation into the stable identity foundation for all later domains.

## Existing functionality to preserve

```text
registration
OTP
email verification
login
JWT access token
refresh token
logout
logout-all
/me
```

## Required improvements

```text
remove/protect insecure user-list endpoint
remove/protect insecure delete-user endpoint
hash OTP
fix JWT secret/config mismatch
fix transaction ownership
restore DB constraints/indexes
canonical repositories/services
rate limiting
role/account status
phone-number support
tests
```

---

# 8. Authentication Implementation Order

Recommended:

```text
1. Lock current behavior with tests
2. Remove critical insecure endpoints
3. Consolidate config/security/database
4. Fix JWT secret handling
5. Fix auth transaction boundaries
6. Hash OTP values
7. Fix OTP/refresh-token DB indexes/constraints
8. Add account status
9. Add USER/ADMIN role
10. Add phone-number uniqueness
11. Establish AuthenticatedIdentity contract
12. Add auth rate limiting
13. Complete integration/security tests
```

Do not rewrite registration/login from scratch unless the existing code cannot be safely adapted.

---

# 9. Milestone 1 Exit Criteria

- [ ] Registration works.
- [ ] OTP verification works securely.
- [ ] Login works.
- [ ] Refresh rotation works.
- [ ] Logout/logout-all work.
- [ ] `/me` is protected.
- [ ] OTP is not stored plaintext.
- [ ] JWT secrets are stable/configured.
- [ ] USER/ADMIN role exists.
- [ ] Account status exists.
- [ ] Phone uniqueness exists or has approved migration path.
- [ ] Insecure endpoints are removed/protected.
- [ ] AuthenticatedIdentity contract exists.
- [ ] Auth tests pass.

---

# 10. Milestone 2 — Profile + Language Foundation

## Goal

Create the learner identity used by matching, pairing, calls, and the social experience.

## Profile work

```text
profile model
profile migration
profile repository
profile application service
self profile API
authenticated public profile API
profile update
interests
profile-completion rule
optional photo support
```

## Language work

```text
languages reference table
English seed/reference
user_languages
mother tongue
spoken languages
learning language
A1–C2 proficiency
```

---

# 11. Milestone 2 Recommended Slices

### Slice A — Core Profile

```text
profiles table
GET /profiles/me
PATCH /profiles/me
GET /profiles/{id}
```

### Slice B — Interests

```text
interests
user_interests
predefined interests
custom interests
```

### Slice C — Language

```text
languages
user_languages
English MVP
A1–C2 validation
```

### Slice D — Profile Completion

```text
ProfileEligibility
```

used by:

```text
Matching
Pairing
```

### Slice E — Profile Photo

Can be parallel because photo is optional.

---

# 12. Milestone 2 Exit Criteria

- [ ] User can retrieve own profile.
- [ ] User can update own profile.
- [ ] Authenticated users can view permitted peer profile.
- [ ] Private auth fields are never exposed.
- [ ] Interests work.
- [ ] Custom interests work.
- [ ] English exists as supported language.
- [ ] A1–C2 works.
- [ ] Profile completeness can be evaluated.
- [ ] Matching-safe profile summary contract exists.
- [ ] Pairing can ask whether profile is complete.
- [ ] Profile/Language tests pass.

---

# 13. Milestone 3 — Matching + Friendship / Blocking

## Goal

Create compatibility discovery and safe peer-interaction relationships before realtime connection.

Two streams may run partly in parallel:

```text
Matching
Friendship / Blocking
```

---

# 14. Matching Work

Implement:

```text
candidate query
self exclusion
account/profile eligibility
English-practice eligibility
block exclusion
interest-based score
profession signal
proficiency signal
stable ranking
maximum 20
safe match response
```

Do not add AI matching.

---

# 15. Friendship / Blocking Work

Implement:

```text
user_blocks
InteractionEligibility
friend_requests
friendships
send request
accept
reject
cancel
remove
friends list
max 20
```

Priority:

```text
blocking + eligibility
```

must be available before realtime messaging/calling.

---

# 16. Milestone 3 Exit Criteria

- [ ] Matching returns safe compatible candidates.
- [ ] Maximum 20 is enforced.
- [ ] Self/inactive/incomplete users are excluded.
- [ ] Blocked users are never recommended.
- [ ] Friend request lifecycle works.
- [ ] Friend list works.
- [ ] 20-friend rule works transactionally.
- [ ] Blocking/unblocking works.
- [ ] InteractionEligibility contract exists.
- [ ] Matching and Friendship tests pass.

---

# 17. Milestone 4 — Realtime Foundation

## Goal

Create reusable realtime infrastructure before implementing product-specific WebSocket business behavior.

## Work

```text
Redis client
Redis health handling
authenticated WebSocket endpoint
connection manager
event envelope
event dispatcher
heartbeat
multi-connection support
presence
Pub/Sub abstraction
```

---

# 18. Realtime Implementation Order

```text
1. Redis async connection
2. WebSocket endpoint
3. WebSocket authentication
4. ConnectionManager
5. connection IDs / multi-tab support
6. heartbeat
7. Redis presence
8. presence online/offline
9. event envelope
10. dispatcher
11. Redis Pub/Sub abstraction
```

Do not put Pairing, Messaging, or Call business rules directly into generic WebSocket infrastructure.

---

# 19. Milestone 4 Exit Criteria

- [ ] Authenticated user can connect via WebSocket.
- [ ] Invalid/suspended user is rejected.
- [ ] Multiple sockets per user work.
- [ ] Presence online/offline works.
- [ ] Heartbeat/TTL cleans stale sessions.
- [ ] Redis is used as transient state only.
- [ ] Realtime events have consistent envelope.
- [ ] Local delivery works.
- [ ] Pub/Sub abstraction supports future multiple instances.
- [ ] Presence tests pass.

---

# 20. Milestone 5 — Automatic Pairing

## Goal

Deliver the real-time “find someone to talk to” workflow.

## Work

```text
pairing.join
pairing.leave
waiting queue
availability checks
candidate filtering
reuse Matching score
atomic reservation
disconnect cleanup
pairing.matched
handoff to Call domain
```

Redis owns waiting/reservation state.

PostgreSQL should not become a live pairing queue.

---

# 21. Pairing Critical Risk

Double pairing must be impossible.

Required test:

```text
two concurrent workers
same candidate
only one successful reservation
```

This is a release-critical concurrency test.

---

# 22. Milestone 5 Exit Criteria

- [ ] Eligible user joins queue.
- [ ] Ineligible/offline/busy user is rejected.
- [ ] Blocked users never pair.
- [ ] Matching compatibility is reused.
- [ ] Atomic reservation works.
- [ ] Stale queue entries disappear.
- [ ] Cancel works.
- [ ] Successful pairing returns a peer + call context.
- [ ] Pairing concurrency tests pass.

---

# 23. Milestone 6 — Voice Calling

## Goal

Deliver TalkTribe's core product value: peer-to-peer English voice conversation.

## Work

```text
call state model
manual friend call
paired-user call
call eligibility
ringing
accept
reject
cancel
missed
WebRTC signaling
offer
answer
ICE
STUN
TURN strategy
active call
end call
call duration
call metadata
```

---

# 24. Voice Implementation Order

```text
1. Call domain/state machine
2. Availability locking
3. Manual call start
4. Incoming call event
5. Accept/reject/cancel
6. WebRTC frontend prototype
7. Offer/answer signaling
8. ICE candidate signaling
9. STUN
10. Active-call state
11. End-call flow
12. Call history
13. Pairing → Call integration
14. TURN production fallback
15. Reconnection/failure hardening
```

---

# 25. Milestone 6 Exit Criteria

- [ ] Manual online-friend call works.
- [ ] Automatically paired users can start call flow.
- [ ] Busy/offline/blocked calls are rejected.
- [ ] One active/ringing call per user is enforced.
- [ ] Offer/answer/ICE signaling works.
- [ ] Voice audio connects with WebRTC.
- [ ] STUN works.
- [ ] Production TURN strategy exists.
- [ ] End/cancel/reject/missed states work.
- [ ] Call history/metadata is correct.
- [ ] Call tests pass.

At this point, the **core TalkTribe value proposition exists**.

---

# 26. Milestone 7 — Messaging

## Goal

Add persistent 1:1 chat around the peer relationship.

## Work

```text
direct conversations
participants
messages
WebSocket send
PostgreSQL persistence
offline retrieval
delivery state
read receipts
typing
block enforcement
one-week retention
pagination
```

---

# 27. Messaging Implementation Order

```text
1. Conversation model
2. Conversation access authorization
3. Message model
4. Message history API
5. WebSocket message.send
6. Persist then acknowledge
7. Recipient realtime delivery
8. Offline retrieval
9. Read receipts
10. Typing indicators
11. Retention cleanup
12. Redis Pub/Sub cross-instance validation
```

---

# 28. Milestone 7 Exit Criteria

- [ ] Direct conversation works.
- [ ] Non-participants are denied.
- [ ] Messages persist.
- [ ] WebSocket send works.
- [ ] Offline messages survive.
- [ ] Blocking stops new messages.
- [ ] Delivery/read state works.
- [ ] Typing works.
- [ ] Message pagination works.
- [ ] 7-day retention is enforced.
- [ ] Messaging tests pass.

---

# 29. Milestone 8 — Feedback + Reporting

## Goal

Complete the post-call trust/safety loop.

## Work

```text
call_feedback
rating endpoint
rating aggregate
report endpoint
report reasons
report context
rate limiting
block-after-report UI option
```

---

# 30. Milestone 8 Exit Criteria

- [ ] Eligible call participant can rate peer.
- [ ] Duplicate feedback is prevented.
- [ ] Rating validation works.
- [ ] Profile rating can be derived/displayed if enabled.
- [ ] User can submit report.
- [ ] Report can reference call/conversation context.
- [ ] Reports are durable.
- [ ] Report abuse is rate-limited.
- [ ] Feedback/report tests pass.

---

# 31. Milestone 9 — Admin Moderation

## Goal

Deliver the MVP administrative moderation capability.

## Early Admin foundation should already exist from Auth:

```text
ADMIN role
require_admin
account status
```

## Full work

```text
admin user list
admin user detail
report queue
report detail
resolve
dismiss
suspend
reactivate
session revocation
realtime disconnect
audit log
```

---

# 32. Milestone 9 Exit Criteria

- [ ] Normal user cannot access admin APIs.
- [ ] Admin can list/view approved user data.
- [ ] Admin can review reports.
- [ ] Admin can resolve/dismiss reports.
- [ ] Admin can suspend/reactivate users.
- [ ] Suspension revokes sessions.
- [ ] Suspended user is removed from realtime activity.
- [ ] Sensitive actions are audited.
- [ ] Auth secrets are never exposed.
- [ ] Admin tests pass.

---

# 33. Milestone 10 — MVP Hardening

## Goal

Turn a functionally complete application into a production-ready MVP.

## Security

```text
rate limiting coverage
secret handling
CORS
HTTPS/WSS
safe logs
security headers
Bandit review
authorization review
dependency review
```

## Reliability

```text
health/live
health/ready
database failure handling
Redis failure handling
email failure behavior
WebSocket reconnect
TURN fallback
```

## Testing

```text
unit
integration
API
WebSocket
concurrency
end-to-end core journey
```

## Observability

```text
structured logs
request IDs
error logs
basic metrics
CloudWatch direction
```

## Deployment

```text
Docker
Nginx
EC2
Vercel
PostgreSQL provider
Redis provider
object storage
GitHub Actions
```

## Data protection

```text
backups
restore procedure
production migration process
```

---

# 34. End-to-End MVP Release Test

Before release, validate:

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
matching works
        ↓
blocking rules work
        ↓
both connect realtime
        ↓
both become online
        ↓
both join pairing
        ↓
pairing succeeds once
        ↓
voice call connects
        ↓
call ends
        ↓
feedback/report works
        ↓
admin can moderate report
```

Messaging should also have its own integrated user journey.

---

# 35. Milestone 10 Exit Criteria

- [ ] Critical security findings resolved.
- [ ] All core domain tests pass.
- [ ] Realtime concurrency tests pass.
- [ ] End-to-end user journey passes.
- [ ] HTTPS/WSS configured.
- [ ] TURN strategy validated.
- [ ] Backups configured.
- [ ] Health checks are real.
- [ ] Logs do not leak secrets.
- [ ] CI quality checks pass.
- [ ] Deployment runbook exists.
- [ ] Production migration process exists.

---

# 36. Suggested Parallel Work

## During Milestone 1

Possible in parallel:

```text
frontend auth UI polish
profile UX design
database design validation
```

## During Milestone 2

```text
Profile core
Language reference/data
Interests
Profile photo
```

## During Milestone 3

```text
Matching
Friendship
Blocking
```

## During Milestone 4

```text
Redis/Presence backend
frontend WebSocket provider
early WebRTC prototype
```

## During Milestone 6

```text
Call backend/signaling
WebRTC frontend
Messaging database/API groundwork
```

## During Milestone 8

```text
Feedback
Reporting
Admin moderation frontend
```

Parallel work must still respect hard dependencies.

---

# 37. What Should Be Deferred

Do not add these to the MVP critical path:

```text
Notifications
Practice Sessions
Video Calls
Group Calls
Community Rooms
Challenges
Leaderboards
Streaks
Badges
Rewards
AI Tutor
AI Grammar Feedback
Pronunciation AI
Embedding Matching
Google Login
Complex Analytics
Microservices
Kafka
Kubernetes
```

They remain future roadmap items.

---

# 38. Future Phase A — Notifications

After core P2P connection is stable:

```text
friend request alerts
message alerts
incoming call notifications
email/push preferences
```

Introduce a Notification domain consuming domain/application events.

---

# 39. Future Phase B — Practice Sessions

Possible future:

```text
schedule practice
reminders
session history
calendar
```

This should not be mixed into the MVP Call domain prematurely.

---

# 40. Future Phase C — Video / Communities

Possible:

```text
video calling
groups
community rooms
```

These may require additional realtime/media architecture decisions.

---

# 41. Future Phase D — Gamification

Possible:

```text
streaks
points
leaderboards
badges
rewards
```

These should be based on stable activity events from the core platform.

---

# 42. Future Phase E — AI

Possible:

```text
AI matching
grammar correction
vocabulary suggestions
pronunciation feedback
conversation summary
speaking score
AI tutor
scenario practice
```

Do not introduce AI before enough real product interaction exists to evaluate whether it improves outcomes.

---

# 43. Jira Generation Timing

Do **not** create the entire future backlog now.

Recommended backlog generation:

```text
Create detailed Jira for:
current milestone
+
next milestone
```

Maintain higher-level epics for later milestones.

Example:

If currently in M1:

```text
Detailed:
M1 Auth
M2 Profile/Language

High level:
M3–M10
```

This reduces backlog churn.

---

# 44. Ticket Granularity

Recommended hierarchy:

```text
Epic
  ↓
Story
  ↓
Task / Sub-task
```

A Story should represent a valuable vertical behavior.

Example:

```text
Epic:
User Profile

Story:
Authenticated user can update their profile

Tasks:
- migration/model
- repository
- application service
- API
- frontend form
- authorization
- tests
```

---

# 45. Definition of Ready

A story is ready when it has:

```text
owner/domain
business value
workflow
dependencies
API impact
DB impact
security rules
acceptance criteria
test expectations
```

---

# 46. Definition of Done

A feature/story is not complete when only code exists.

Required:

```text
implementation
validation
authorization
tests
migration if needed
error handling
documentation
lint/type/security checks
review
```

For realtime features also include:

```text
disconnect behavior
concurrency
failure behavior
```

---

# 47. Change Management

New request:

```text
New Requirement / Bug
        ↓
Identify domain
        ↓
Impact requirements?
        ↓
Impact workflow?
        ↓
Impact architecture?
        ↓
If architectural:
new/superseding ADR
        ↓
Update dependencies/roadmap
        ↓
Create Jira issue
        ↓
Implement
        ↓
Tests
        ↓
Docs update
```

Do not quietly modify architecture based on one ticket.

---

# 48. Recommended Development Branch Strategy

For each implementation slice:

```text
main
 ↓
feature branch
 ↓
implementation + tests
 ↓
PR
 ↓
review
 ↓
merge
```

When a new feature depends on an unmerged feature:

Prefer waiting for the dependency to merge when practical.

If work must continue:

```text
branch from dependency branch
```

but rebase/retarget carefully after the dependency merges.

Avoid long dependency chains of unmerged branches.

---

# 49. Roadmap Tracking Status

Suggested planning status:

| Milestone | Status |
|---|---|
| M0 Engineering Baseline | In progress / verify current repo |
| M1 Authentication Stabilization | Partially implemented |
| M2 Profile + Language | Planned |
| M3 Matching + Friendship/Blocking | Planned |
| M4 Realtime Foundation | Planned |
| M5 Pairing | Planned |
| M6 Voice Calls | Planned |
| M7 Messaging | Planned |
| M8 Feedback + Reporting | Planned |
| M9 Admin Moderation | Planned |
| M10 MVP Hardening | Planned |

Do not mark a milestone complete based only on folder existence.

---

# 50. Immediate Next Implementation Focus

Given the current project history, the next implementation focus should be:

```text
M0/M1
Engineering cleanup
+
Authentication stabilization
```

before starting large Profile/Matching/Realtime implementations.

The architecture refactor has begun, but behavior and tests must be verified against the current repository.

---

# 51. Planning Artifacts After This Roadmap

```text
Requirements                   ✅
Architecture                   ✅
Workflows                      ✅
Feature Dependencies           ✅
Development Roadmap            ✅
        ↓
FEATURE_CATALOG.md             ← NEXT
        ↓
EPIC_CATALOG.md
        ↓
JIRA_GENERATION_RULES.md
        ↓
DEFINITION_OF_DONE.md
        ↓
Stories / Tasks
        ↓
Jira
        ↓
Implementation
```

---

# 52. Final Roadmap Diagram

```text
M0 ENGINEERING BASELINE
        ↓
M1 AUTH STABILIZATION
        ↓
M2 PROFILE + LANGUAGE
        ↓
M3 MATCHING + FRIENDSHIP/BLOCKING
        ↓
M4 REDIS + WEBSOCKET + PRESENCE
        ↓
M5 AUTOMATIC PAIRING
        ↓
M6 VOICE CALLS
        ↓
M7 MESSAGING
        ↓
M8 FEEDBACK + REPORTING
        ↓
M9 ADMIN MODERATION
        ↓
M10 MVP HARDENING
        ↓
PRODUCTION MVP
        ↓
NOTIFICATIONS / SESSIONS / VIDEO / GAMIFICATION / AI
```
