# TalkTribe Jira Generation Rules

**Stage:** 5 — Jira Backlog Preparation  
**Status:** Backlog-generation baseline  
**Purpose:** Define consistent rules for converting TalkTribe planning artifacts into Jira Epics, Stories, Tasks, Subtasks, Bugs, and implementation-ready tickets.

**Depends on:**
- `FEATURE_CATALOG.md`
- `EPIC_CATALOG.md`
- `DEVELOPMENT_ROADMAP.md`
- `FEATURE_DEPENDENCIES.md`
- Stage 3 workflow documents
- `TARGET_ARCHITECTURE.md`

---

# 1. Purpose

This document defines how Jira work should be generated for TalkTribe.

It answers:

- Which Jira issue types should be used?
- How should Epics, Stories, Tasks, Bugs, and Subtasks be separated?
- What information must every implementation ticket contain?
- How should acceptance criteria be written?
- How should dependencies be recorded?
- How much backlog should be generated at one time?
- How should technical work be represented without losing business context?
- How should bugs and architecture changes be handled?
- How should Jira stay aligned with requirements and architecture?

Jira is the execution system.

It is **not** the source of truth for product architecture.

Primary sources remain:

```text
Requirements
Architecture
ADRs
Workflows
Feature Dependencies
Roadmap
Feature Catalog
Epic Catalog
```

---

# 2. Jira Hierarchy

Recommended hierarchy:

```text
Epic
  ↓
Story
  ↓
Task / Subtask
```

Separate issue type:

```text
Bug
```

Use these meanings consistently.

---

# 3. Epic

An Epic represents:

```text
a meaningful product or engineering outcome
```

Examples:

```text
Authentication & Account Security
User Profile Management
Automatic Co-Learner Pairing
Peer-to-Peer Voice Calling
```

Do not use Epics for:

```text
one endpoint
one migration
one class
one unit test
```

These belong under Stories/Tasks.

---

# 4. Story

A Story represents:

```text
observable user/system behavior
```

Preferred format:

```text
As a <user/system role>,
I want <capability>,
so that <business outcome>.
```

Example:

```text
As a learner,
I want to accept an incoming friend request,
so that the requester and I become connected.
```

System-oriented story is also valid:

```text
As the pairing system,
I need to atomically reserve two users,
so that no user can be paired with multiple peers at the same time.
```

---

# 5. Task

A Task represents:

```text
technical work required to deliver a Story
```

Examples:

```text
Create profile migration
Implement ProfileRepository
Add PATCH /profiles/me
Add profile update tests
Create frontend profile form
```

A Task should not replace a Story when user/system behavior exists.

---

# 6. Subtask

Use Subtasks when a Task still needs small execution steps.

Example:

```text
Task:
Implement profile photo upload

Subtasks:
- Add StorageService interface
- Add storage adapter
- Add file validation
- Add upload endpoint
- Add tests
```

Avoid excessive decomposition where every tiny code change becomes a Subtask.

---

# 7. Bug

Use Bug for:

```text
behavior that violates existing expected behavior
```

Examples:

```text
OTP can be reused after verification
Blocked user can still send messages
Pairing can reserve same user twice
Refresh token remains valid after logout
```

Do not create a Feature Story for something that is clearly a defect.

---

# 8. Architecture Change

Architecture changes should not be introduced only through a Jira task.

Flow:

```text
Architecture problem/change
        ↓
Impact analysis
        ↓
ADR if architectural decision changes
        ↓
Update architecture/workflow docs
        ↓
Create Jira implementation issue
```

Jira implements the architecture decision.

It does not silently define it.

---

# 9. Backlog Generation Scope

Do not generate detailed tickets for the entire project at once.

Recommended:

```text
Detailed:
current milestone
+
next milestone

High-level:
later epics only
```

Example:

If currently implementing M1:

```text
Detailed:
M1 Auth
M2 Profile + Language

High-level only:
M3–M10
```

This reduces stale backlog work.

---

# 10. Jira IDs

Do not manually reserve Jira issue keys.

Jira assigns:

```text
TT-101
TT-102
TT-103
...
```

The key does not represent implementation order.

Example:

```text
TT-120 may depend on TT-117
```

That is normal.

Dependencies should be recorded explicitly.

---

# 11. Internal Planning IDs

Keep planning IDs separate from Jira issue keys.

Examples:

```text
AUTH-01
PROF-03
PAIR-05
CALL-07
```

These identify catalog features.

A Jira Story may reference:

```text
Feature ID: PAIR-05
```

while Jira itself assigns:

```text
TT-214
```

---

# 12. Ticket Title Rules

Titles should be:

```text
specific
action-oriented
short enough to scan
```

Good:

```text
Add email OTP verification
Prevent duplicate pending friend requests
Implement profile completion eligibility
Add authenticated WebSocket handshake
Atomically reserve paired users
```

Avoid:

```text
Auth work
Backend updates
Fix feature
Do database things
Implement everything for profile
```

---

# 13. Story Ticket Template

Every Story should contain:

```text
Title
Epic
Feature ID(s)
Milestone
Priority

Description
User Story
Business Context
Scope
Out of Scope

Dependencies
Architecture References
Workflow References

Acceptance Criteria

Technical Notes
API Impact
Database Impact
Security / Authorization
Realtime Considerations
Observability

Test Requirements

Definition of Done
Open Decisions / Risks
```

Not every section needs long content, but relevant sections should not be omitted.

---

# 14. Story Description

Describe:

```text
what behavior is needed
why it matters
where it belongs
```

Example:

```text
Add the ability for an authenticated learner to update their own profile.
The operation must use the Profile domain, enforce ownership, validate fields,
and return the updated safe self-profile representation.
```

---

# 15. Business Context

Explain why the Story exists.

Example:

```text
A completed learner profile is required before Matching and Pairing can evaluate compatibility.
```

This keeps technical work connected to product value.

---

# 16. Scope

Explicitly state what is included.

Example:

```text
In scope:
- update bio
- profession
- location
- profile-owned display fields
- validation
- response schema
```

---

# 17. Out of Scope

State what should **not** be implemented in this Story.

Example:

```text
Out of scope:
- language update
- profile photo upload
- achievements
- rewards
```

This prevents scope creep.

---

# 18. Dependencies

Every dependency should use one of:

```text
Blocks
Blocked by
Relates to
Requires feature
```

Example:

```text
Blocked by:
AUTH-09 AuthenticatedIdentity
PROF-01 Own Profile Retrieval
```

Once Jira keys exist, link them inside Jira too.

---

# 19. Architecture References

Reference relevant documents.

Example:

```text
TARGET_ARCHITECTURE.md
DATABASE_ARCHITECTURE.md
API_ARCHITECTURE.md
SECURITY_ARCHITECTURE.md
```

Do not paste entire architecture files into Jira.

Link/reference the relevant decision.

---

# 20. Workflow References

Every user-facing/core system Story should point to its workflow.

Examples:

```text
PROFILE_WORKFLOW.md
PAIRING_WORKFLOW.md
VOICE_CALL_WORKFLOW.md
```

This ensures implementation matches approved behavior.

---

# 21. Acceptance Criteria

Acceptance Criteria describe externally verifiable behavior.

Preferred style:

```text
Given
When
Then
```

Example:

```text
Given an authenticated learner owns profile 123
When they submit valid profile updates
Then the profile is updated
And the API returns the updated profile
```

---

# 22. Acceptance Criteria Rules

Acceptance Criteria should be:

```text
specific
testable
observable
unambiguous
```

Avoid:

```text
Works correctly
Handles errors
Secure
Fast
Good UX
```

Replace with concrete behavior.

---

# 23. Acceptance Criteria Example — Blocking

```text
Given User A has blocked User B
When Matching evaluates User B as a candidate for User A
Then User B is excluded from the result set.
```

```text
Given either user has blocked the other
When one attempts to start a voice call
Then the request is rejected with an interaction-not-allowed error.
```

---

# 24. Technical Notes

Technical Notes may include:

```text
service/interface to use
transaction boundary
repository behavior
expected design pattern
performance/concurrency requirement
```

Do not prescribe every internal line of code unless necessary.

---

# 25. API Impact Section

If API changes:

```text
Method
Path
Request schema
Response schema
Status codes
Authorization
Error codes
```

Example:

```text
PATCH /api/v1/profiles/me
```

If no API change:

```text
API Impact: None
```

---

# 26. Database Impact Section

Include:

```text
new table
column changes
constraints
indexes
migration
data backfill
cascade behavior
```

Example:

```text
Add unique normalized friendship pair constraint.
```

Never create schema manually outside Alembic in normal development.

---

# 27. Security / Authorization Section

Every protected Story should answer:

```text
Who can call this?
Who owns the resource?
What role is required?
What data must not be exposed?
What rate limit applies?
```

Example:

```text
Only the incoming request receiver may accept a friend request.
```

---

# 28. Realtime Considerations

For WebSocket/Redis features include:

```text
authentication
event type
event authorization
disconnect behavior
retry/idempotency
Redis state
TTL
multi-device
multi-instance behavior
```

---

# 29. Concurrency Requirements

Explicitly call out concurrency-sensitive Stories.

Examples:

```text
FRIEND-08 Maximum 20 friends
PAIR-05 Atomic reservation
CALL-12 One active call per user
```

These Stories must include concurrent tests.

---

# 30. Observability

Where useful, define:

```text
safe logs
metrics
error events
audit logs
```

Example:

```text
Admin suspension should log:
admin_user_id
target_user_id
action
request_id
```

Never log:

```text
password
JWT
OTP
refresh token
```

---

# 31. Test Requirements

Every implementation Story needs tests.

Possible categories:

```text
unit
integration
API
authorization
database
WebSocket
concurrency
frontend
```

Example:

```text
Tests:
- owner can update profile
- another user cannot update profile
- invalid proficiency rejected
- DB rollback occurs on failure
```

---

# 32. Definition of Done

Every Story inherits the global `DEFINITION_OF_DONE.md`.

Add Story-specific requirements only where needed.

Example:

```text
Story-specific DoD:
- concurrency test proves no double reservation
- Redis queue has stale-entry cleanup
```

---

# 33. Open Decisions

If a Story depends on an unresolved product decision, do not silently invent it.

Mark:

```text
BLOCKED_BY_DECISION
```

Example:

```text
Exact proficiency scoring is not finalized.
```

Either:

1. resolve before implementation, or
2. slice the Story so unaffected work can proceed.

---

# 34. Priority Rules

Recommended:

```text
Critical
High
Medium
Low
```

## Critical

Blocks core MVP path.

Examples:

```text
Auth security
Profile completion
Blocking
WebSocket auth
Pairing atomic reservation
Voice signaling
```

## High

Required MVP but not always on shortest path.

Examples:

```text
Messaging
Feedback
Admin moderation
```

## Medium

Useful MVP polish.

Examples:

```text
profile photo
matching explanation
secondary UI improvements
```

## Low

Nonessential polish / later improvement.

---

# 35. Story Size

A Story should normally fit one coherent behavior.

Too large:

```text
Build complete Authentication System
```

Better:

```text
Register a user
Verify registration OTP
Login verified user
Rotate refresh token
Logout current session
```

---

# 36. Avoid Horizontal-Only Stories

Avoid backlog made entirely of:

```text
Create models
Create repositories
Create services
Create routes
```

Prefer vertical Stories.

Example:

```text
Story:
User can block another user
```

Tasks:

```text
migration
model
repository
service
API
tests
frontend
```

---

# 37. When Technical Stories Are Valid

Technical Stories are valid when they provide platform capability.

Examples:

```text
Authenticated WebSocket foundation
Redis Pub/Sub abstraction
Canonical database/session layer
Test infrastructure
```

These may not have a normal end-user user story.

Use system/business outcome instead.

---

# 38. Bug Ticket Template

Bug should contain:

```text
Title
Environment
Observed Behavior
Expected Behavior
Steps to Reproduce
Impact
Severity
Affected Feature / Epic
Root Cause (after investigation)
Fix Approach
Regression Tests
Security Impact
```

---

# 39. Bug Severity

Suggested:

```text
Critical
High
Medium
Low
```

Critical examples:

```text
auth bypass
private data exposure
double pairing causing wrong call
password/token exposure
```

High:

```text
core feature broken
blocked users can communicate
refresh token security failure
```

---

# 40. Bug vs Story

Use Bug when:

```text
approved behavior exists
implementation violates it
```

Use Story when:

```text
behavior does not exist yet
```

---

# 41. Refactoring Tickets

Refactoring should state:

```text
why
scope
behavior that must remain unchanged
tests protecting behavior
architecture improvement
```

Example:

```text
Refactor Auth into modular domain structure without changing existing API behavior.
```

Never use a vague ticket:

```text
Clean backend
```

---

# 42. Migration Tickets

For nontrivial migrations include:

```text
forward migration
existing-data handling
rollback strategy
deployment order
compatibility period
```

Especially important for:

```text
phone-number introduction
password column rename
account status
role
```

---

# 43. Frontend Ticket Rules

Frontend Stories should reference the same behavior as backend.

Avoid independent feature definitions.

Example:

Backend Story:

```text
Learner can enter pairing queue
```

Frontend Story:

```text
Learner can start/cancel Talk Now search and see waiting/matched state
```

Both depend on `PAIRING_WORKFLOW.md`.

---

# 44. Backend / Frontend Split

For small features, one Story can include both.

For larger features, separate Stories may be useful.

Example:

```text
Story A:
Backend supports WebRTC call signaling

Story B:
Frontend establishes WebRTC audio connection
```

Both live under Voice Call Epic.

---

# 45. Infrastructure Tickets

Infrastructure tickets should state the product capability they unlock.

Bad:

```text
Install Redis
```

Better:

```text
Add Redis application client for Presence and Pairing transient state
```

---

# 46. Story Dependency Example

```text
EPIC-08 Pairing

Story 1:
User can join pairing queue

Blocked by:
- authenticated WebSocket
- Presence
- profile eligibility

Story 2:
System atomically reserves compatible users

Blocked by:
- waiting queue
- matching compatibility
- InteractionEligibility

Story 3:
Pairing hands users to Call domain

Blocked by:
- atomic reservation
- Call context creation
```

---

# 47. Recommended Ticket Ordering

Within a feature:

```text
1. Contract / behavior
2. Database migration if required
3. Application/domain behavior
4. API/realtime transport
5. Frontend integration
6. Tests/hardening
```

Tests should be developed throughout, not literally last.

---

# 48. Ticket Naming Examples

## Auth

```text
Add role and account status to authenticated identity
Hash OTP values before persistence
Rate-limit OTP verification attempts
```

## Profile

```text
Allow learner to complete profile
Expose safe authenticated peer profile
Add predefined and custom interests
```

## Pairing

```text
Allow learner to join English pairing queue
Atomically reserve compatible waiting users
Remove disconnected learners from pairing queue
```

## Calls

```text
Allow online friends to start voice calls
Relay authorized WebRTC offer and answer events
Prevent users from joining multiple active calls
```

---

# 49. Jira Labels

Suggested labels should remain limited and useful.

Examples:

```text
backend
frontend
database
security
realtime
websocket
redis
webrtc
testing
infrastructure
mvp
```

Do not create dozens of overlapping labels.

---

# 50. Components

If Jira Components are used, suggested:

```text
Auth
Profile
Language
Matching
Friendship
Realtime
Presence
Pairing
Calls
Messaging
Feedback
Admin
Platform
Frontend
```

Use Components for ownership, Labels for technical/cross-cutting traits.

---

# 51. Milestone / Fix Version

If Jira versions/releases are used:

```text
M0
M1
M2
...
M10
```

or a release name:

```text
TalkTribe MVP
```

Avoid inventing dates before release planning exists.

---

# 52. Story Points / Estimates

Do not use Story Points to encode priority.

If estimating:

```text
estimate complexity/effort
```

Priority is separate.

Do not estimate unresolved Stories until enough detail exists.

---

# 53. Definition of Ready in Jira

Story should not move to Ready until:

- [ ] Requirements are understood.
- [ ] Owning Epic is known.
- [ ] Feature ID is known.
- [ ] Dependencies are known.
- [ ] Acceptance Criteria exist.
- [ ] API/DB impact is understood.
- [ ] Security rules exist.
- [ ] Required product decisions are resolved.
- [ ] Test expectations exist.

---

# 54. Suggested Jira Workflow

Simple workflow:

```text
Backlog
   ↓
Ready
   ↓
In Progress
   ↓
Code Review
   ↓
Testing
   ↓
Done
```

Optional:

```text
Blocked
```

Do not create an overly complex Jira workflow for a small project.

---

# 55. "Done" Rule

A ticket is not Done because:

```text
code compiles
endpoint exists
PR opened
```

Done means:

```text
merged
acceptance criteria satisfied
tests passing
required docs updated
migration handled
security checked
```

Exact shared criteria are defined in `DEFINITION_OF_DONE.md`.

---

# 56. Pull Request Linkage

Each implementation PR should reference its Jira issue.

Example:

```text
TT-123
```

PR description should state:

```text
what changed
tests
migration impact
security impact
screenshots if frontend
```

---

# 57. Commit Messages

Recommended:

```text
TT-123 Add profile completion validation
```

or project-agreed equivalent.

One Jira issue may contain multiple commits.

Do not force one commit per ticket.

---

# 58. Rebase / Force Push

If a PR branch is rebased after review:

```text
git push --force-with-lease
```

is preferred over unrestricted force push.

The existing PR normally updates because the PR tracks the branch.

This Git behavior is separate from Jira issue state.

---

# 59. Jira and Documentation Synchronization

When implementation changes approved behavior:

```text
update requirement/workflow/ADR first or alongside
```

Then update Jira.

When Jira only implements already-approved behavior:

```text
no architecture rewrite needed
```

---

# 60. Requirements Traceability

A Story should be traceable:

```text
Requirement
   ↓
Workflow
   ↓
Feature ID
   ↓
Epic
   ↓
Story
   ↓
Task
   ↓
PR/Test
```

Example:

```text
Requirement:
Users can block peers

Workflow:
FRIENDSHIP_WORKFLOW.md

Feature:
BLOCK-01

Epic:
EPIC-05

Story:
Learner can block another user

Tasks:
DB + service + API + tests

PR:
TT-xxx
```

---

# 61. AI-Assisted Ticket Generation

When using Claude/ChatGPT to generate Jira work, provide:

```text
relevant requirements
workflow
feature IDs
epic
dependency rules
architecture constraints
ticket template
```

Do not ask:

```text
"Create all Jira tickets for my app"
```

without context.

---

# 62. Recommended AI Prompt Structure

```text
You are generating Jira Stories for TalkTribe.

Source of truth:
- FEATURE_CATALOG.md
- EPIC_CATALOG.md
- relevant workflow
- FEATURE_DEPENDENCIES.md
- architecture documents

Generate Stories only for:
<current epic/milestone>

For each Story include:
- title
- feature IDs
- description
- user story
- business context
- in scope
- out of scope
- dependencies
- acceptance criteria
- API impact
- DB impact
- security
- tests
- DoD

Do not invent unresolved product decisions.
Mark blocked items explicitly.
```

---

# 63. Jira Generation Review Checklist

Before creating issues:

- [ ] No duplicate Story already exists.
- [ ] Correct Epic selected.
- [ ] Correct feature IDs referenced.
- [ ] Story is not too large.
- [ ] Story is not merely a coding layer.
- [ ] Dependencies are explicit.
- [ ] Acceptance Criteria are testable.
- [ ] Security is addressed.
- [ ] DB/API impacts are clear.
- [ ] Open decisions are not silently invented.
- [ ] Story belongs to current/next milestone.

---

# 64. Example Complete Story

## Title

```text
Allow learner to accept an incoming friend request
```

## Epic

```text
EPIC-05 — Friendship & Blocking
```

## Feature ID

```text
FRIEND-03
```

## Milestone

```text
M3
```

## User Story

```text
As a learner,
I want to accept an incoming friend request,
so that the requester and I become friends.
```

## Business Context

```text
Friendship is required for friend lists and manual friend voice calls.
```

## In Scope

```text
receiver authorization
pending-state validation
block validation
20-friend checks
friendship creation
request status update
```

## Out of Scope

```text
notifications
suggested matching changes
manual voice-call implementation
```

## Dependencies

```text
FRIEND-01
BLOCK-03
AuthenticatedIdentity
```

## Acceptance Criteria

```text
Given an authenticated user is the receiver of a PENDING request
And neither user has blocked the other
And both users have fewer than 20 friends
When the receiver accepts the request
Then exactly one friendship is created
And the request becomes ACCEPTED.
```

```text
Given either user has reached the 20-friend limit
When acceptance is attempted
Then no friendship is created
And the request is not incorrectly marked ACCEPTED.
```

```text
Given a user who is not the receiver
When they attempt to accept the request
Then access is denied.
```

## Database Impact

```text
friendships
friend_requests
transaction + concurrency protection
```

## Security

```text
Only request receiver may accept.
Block state must be checked.
```

## Tests

```text
happy path
unauthorized user
non-pending state
blocked pair
friend limit
concurrent acceptance
```

---

# 65. Backlog Creation Order

Recommended:

```text
1. Create/confirm MVP Epics
2. Generate Stories for current milestone
3. Review product decisions
4. Generate Stories for next milestone
5. Create technical Tasks only when Stories are implementation-ready
6. Implement
7. Update roadmap as actual project state changes
```

---

# 66. Next Planning Artifact

```text
Requirements                   ✅
Architecture                   ✅
Workflows                      ✅
Feature Dependencies           ✅
Development Roadmap            ✅
Feature Catalog                ✅
Epic Catalog                   ✅
JIRA_GENERATION_RULES.md       ✅
        ↓
DEFINITION_OF_DONE.md          ← NEXT
        ↓
Detailed Stories / Tasks
        ↓
Jira
        ↓
Implementation
```
