# TalkTribe Database Architecture

**Status:** Stage 2 architecture design  
**Architecture style:** Modular Monolith  
**Primary database:** PostgreSQL  
**Supporting transient store:** Redis  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `DOMAIN_BOUNDARIES.md`, `COMPONENT_ARCHITECTURE.md`

---

## 1. Purpose

This document defines the target database architecture for TalkTribe MVP.

It establishes:

- database ownership by domain
- target tables and relationships
- durable vs transient data
- constraints and indexes
- transaction boundaries
- retention rules
- deletion behavior
- migration strategy
- current-auth migration concerns
- which data belongs in PostgreSQL and which belongs in Redis

This document does not define API endpoints or WebSocket event formats.

---

## 2. Database Principles

1. PostgreSQL is the primary durable system of record.
2. Redis is used only for transient/distributed state.
3. Each domain owns its own persistence model.
4. A domain must not directly update another domain's tables.
5. Foreign keys should enforce durable relational integrity where appropriate.
6. Business rules that can be safely enforced at the database level should use constraints.
7. Indexes should support actual query patterns, not be added blindly.
8. Application services own transaction boundaries.
9. Repositories should not commit independently.
10. Alembic is the source of truth for schema migrations.
11. Schema changes must be backward-safe where practical.
12. Data retention/deletion behavior must be explicit.

---

# 3. Current Database State

The current implementation already contains:

```text
users
otps
refresh_tokens
```

Known current issues from the architecture review:

- OTP values are stored in plaintext.
- `otps.user_id` lost `ON DELETE CASCADE` in a later migration.
- OTP lookup indexes were removed.
- `refresh_tokens.user_id` needs an index for user-based revocation queries.
- Duplicate/unused indexes exist on primary-key columns.
- Transaction ownership is inconsistent.
- `users.password` stores a hash but is named `password`.
- User/account/profile concerns are currently mixed in one table/model.
- Two database/session infrastructure implementations previously existed and should be consolidated.

The migration to the target structure should preserve working authentication behavior.

---

# 4. Durable vs Transient Data

## PostgreSQL

Use PostgreSQL for durable business data:

- user/account identity
- profile
- language/proficiency
- interests
- friend requests
- friendships
- blocks
- conversations
- messages
- voice-call history/metadata where required
- admin/moderation records
- refresh tokens
- OTP verification records if retained in SQL

## Redis

Use Redis for transient/distributed state:

- online/offline presence
- active WebSocket connection state
- Pub/Sub
- typing indicators
- rate-limit counters
- temporary call-signaling state
- call ringing/ephemeral coordination
- short-lived caches

Redis must not become the only copy of durable business history.

---

# 5. MVP Domain-Owned Tables

Recommended MVP table groups:

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
└── voice_calls

Admin
├── user_reports
└── admin_audit_logs   # if included in MVP admin scope
```

Not every table must be created immediately. Create tables only when the related feature is implemented.

---

# 6. Auth Domain

## 6.1 `users`

Purpose:

Stores authentication/account identity.

Recommended columns:

```text
id
username
email
phone_number
password_hash
role
account_status
is_verified
created_at
updated_at
```

### Notes

Current registration requirements include:

- username
- email
- password
- full name
- phone number is required in the target product decision

`full_name` should preferably belong to Profile rather than Auth if the profile module owns presentation/user-facing identity. During migration it may temporarily remain on `users` to avoid breaking current behavior.

### Recommended constraints

```text
PRIMARY KEY (id)
UNIQUE (username)
UNIQUE (email)
UNIQUE (phone_number)
NOT NULL username
NOT NULL email
NOT NULL phone_number
NOT NULL password_hash
NOT NULL role
NOT NULL account_status
NOT NULL is_verified
```

### Role

Initial roles:

```text
USER
ADMIN
```

Prefer an application enum and database check/enum strategy chosen consistently.

### Account status

Recommended concept:

```text
PENDING_VERIFICATION
ACTIVE
SUSPENDED
BLOCKED
DELETED
```

Exact enum values must be finalized in Security Architecture.

This is clearer than overloading only `is_active`.

---

## 6.2 `otps`

Purpose:

Stores short-lived verification records.

Recommended columns:

```text
id
user_id
otp_hash
purpose
expires_at
attempt_count
is_used
created_at
used_at
```

### Important

Do not store plaintext OTP values.

Use a one-way representation suitable for OTP verification.

### Purpose values

Examples:

```text
REGISTRATION
PASSWORD_RESET
EMAIL_CHANGE
```

Only purposes actually implemented should be enabled.

### Recommended indexes

```text
(user_id, purpose, is_used)
expires_at
```

### Foreign key

```text
user_id → users.id ON DELETE CASCADE
```

### Retention

Expired/used OTP rows should be periodically cleaned.

Exact cleanup window can be defined operationally.

---

## 6.3 `refresh_tokens`

Purpose:

Tracks refresh-token/session lifecycle.

Recommended columns:

```text
id
user_id
token_hash_or_jti
expires_at
is_revoked
created_at
revoked_at
```

### Important

Prefer not to store raw refresh tokens if revocation can be implemented using a secure hash or token identifier.

### Recommended indexes

```text
UNIQUE(token_hash_or_jti)
(user_id, is_revoked)
expires_at
```

### Foreign key

```text
user_id → users.id ON DELETE CASCADE
```

---

# 7. Profile Domain

## 7.1 `profiles`

Purpose:

Stores user-facing profile information.

Recommended columns:

```text
user_id
full_name
profile_photo_url
bio
profession
location
mother_tongue_display_or_reference
preferred_call_duration
preferred_partner
created_at
updated_at
```

### Mandatory vs optional

Current agreed optional fields:

```text
profile_photo_url
bio
profession
location
```

Other MVP-required fields should be represented as required once their exact list is finalized.

### Primary key strategy

Recommended:

```text
PRIMARY KEY (user_id)
FOREIGN KEY user_id → users.id ON DELETE CASCADE
```

This models a one-to-one account/profile relationship.

---

# 8. Interests

## 8.1 `interests`

Purpose:

Stores predefined and approved/custom interests.

Recommended columns:

```text
id
name
is_predefined
created_by_user_id   # nullable
is_active
created_at
```

### Constraints

```text
UNIQUE normalized interest name
```

Custom interests should be normalized to avoid duplicates such as:

```text
Photography
photography
 photography 
```

The exact moderation policy for custom interests is future product/admin detail.

---

## 8.2 `user_interests`

Purpose:

Many-to-many relation between users/profiles and interests.

Recommended columns:

```text
user_id
interest_id
created_at
```

Recommended key:

```text
PRIMARY KEY (user_id, interest_id)
```

Foreign keys:

```text
user_id → users.id ON DELETE CASCADE
interest_id → interests.id
```

Recommended index:

```text
interest_id
```

This supports matching candidates by shared interests.

---

# 9. Language Domain

## 9.1 `languages`

Purpose:

Language master data.

Recommended columns:

```text
id
code
name
is_active
created_at
```

Example MVP row:

```text
en | English
```

### Constraints

```text
UNIQUE(code)
UNIQUE(name)
```

Even though MVP supports only English, storing it as master data avoids redesign when new languages are added.

---

## 9.2 `user_languages`

Purpose:

Stores the relationship between a user and a language.

Recommended columns:

```text
id
user_id
language_id
relationship_type
proficiency_level
is_primary
created_at
updated_at
```

Possible relationship types:

```text
NATIVE
SPEAKS
LEARNING
```

Possible proficiency values:

```text
A1
A2
B1
B2
C1
C2
```

### Constraints

At minimum:

```text
UNIQUE(user_id, language_id, relationship_type)
```

### Indexes

```text
(user_id)
(language_id, relationship_type, proficiency_level)
```

These support profile retrieval and matching queries.

### Open product decision

The exact rules for multiple native/learning languages remain open.

MVP can enforce simpler rules in the application layer while keeping the schema extensible.

---

# 10. Friendship / Connection Domain

## 10.1 `friend_requests`

Purpose:

Stores pending/history of connection requests.

Recommended columns:

```text
id
sender_user_id
receiver_user_id
status
created_at
responded_at
```

Statuses:

```text
PENDING
ACCEPTED
REJECTED
CANCELLED
```

### Constraints

- sender and receiver cannot be the same user
- only one active pending request for the same pair

Possible implementation:

```text
CHECK(sender_user_id <> receiver_user_id)
```

Pair uniqueness may need normalized pair logic or a partial unique index for `PENDING`.

---

## 10.2 `friendships`

Purpose:

Stores accepted friend relationships.

Recommended columns:

```text
id
user_low_id
user_high_id
created_at
```

Store the smaller user ID in `user_low_id` and larger in `user_high_id`.

This prevents duplicate symmetrical friendships:

```text
(A, B)
(B, A)
```

### Constraints

```text
CHECK(user_low_id < user_high_id)
UNIQUE(user_low_id, user_high_id)
```

### Indexes

Indexes should support lookup by either side:

```text
user_low_id
user_high_id
```

### Friend limit

Business rule:

```text
Maximum 20 friends per user
```

This should be enforced transactionally in the Friendship application layer.

A simple database constraint cannot enforce a cross-row count safely by itself.

---

## 10.3 `user_blocks`

Purpose:

Stores user-to-user blocking.

Recommended columns:

```text
blocker_user_id
blocked_user_id
created_at
```

Key:

```text
PRIMARY KEY(blocker_user_id, blocked_user_id)
CHECK(blocker_user_id <> blocked_user_id)
```

Blocking is directional.

If A blocks B, interaction must be denied according to business rules even if B has not blocked A.

---

# 11. Messaging Domain

## 11.1 `conversations`

Purpose:

Durable conversation identity.

Recommended columns:

```text
id
conversation_type
created_at
updated_at
```

For MVP:

```text
DIRECT
```

Group conversation types can be introduced later.

---

## 11.2 `conversation_participants`

Purpose:

Maps users to conversations.

Recommended columns:

```text
conversation_id
user_id
joined_at
left_at
```

Recommended key:

```text
PRIMARY KEY(conversation_id, user_id)
```

For direct MVP conversations, application/database rules should ensure exactly two active participants.

---

## 11.3 `messages`

Purpose:

Stores durable chat messages.

Recommended columns:

```text
id
conversation_id
sender_user_id
content
sent_at
delivered_at
read_at
deleted_at
```

### Current MVP decisions

- one-to-one messaging
- message persistence
- typing indicator
- read receipts
- message history retained for **1 week**

### Indexes

Critical query patterns:

```text
(conversation_id, sent_at DESC)
(sender_user_id)
sent_at
```

### Retention

Messages older than one week should be deleted according to the agreed product requirement.

Do not rely solely on client behavior.

A scheduled cleanup/background job should enforce retention.

### Open decision

Whether message deletion should be hard-delete or tombstone/soft-delete is not yet finalized.

---

# 12. Voice Call Domain

Voice calling is a core MVP capability.

## 12.1 `voice_calls`

Purpose:

Stores durable call metadata/history where needed.

Recommended columns:

```text
id
caller_user_id
callee_user_id
status
started_at
answered_at
ended_at
duration_seconds
ended_by_user_id
created_at
```

Potential statuses:

```text
RINGING
ACCEPTED
REJECTED
MISSED
CANCELLED
ENDED
FAILED
```

Exact call state machine belongs in `REALTIME_ARCHITECTURE.md`.

### Important

Do **not** store voice media in PostgreSQL.

The audio stream is WebRTC peer-to-peer.

PostgreSQL stores metadata only.

### Indexes

```text
(caller_user_id, created_at DESC)
(callee_user_id, created_at DESC)
status
```

### Stats

User profile stats such as:

```text
Calls
Call Time
Rating
```

should ideally be calculated from source records or maintained through explicit derived/statistics logic rather than duplicated arbitrarily.

---

# 13. Rating / Feedback

The core user journey includes rating/reporting after talking with a co-learner.

This should be recognized in the database design.

## 13.1 `call_feedback`

Recommended columns:

```text
id
call_id
reviewer_user_id
reviewed_user_id
rating
feedback_text
created_at
```

### Constraints

Example:

```text
rating between 1 and 5
one feedback record per reviewer per call
reviewer_user_id <> reviewed_user_id
```

Whether free-text feedback is MVP should follow final product scope.

---

## 13.2 `user_reports`

Purpose:

User reports are needed for moderation/admin.

Recommended columns:

```text
id
reporter_user_id
reported_user_id
call_id          # nullable
conversation_id  # nullable
reason
details
status
created_at
resolved_at
resolved_by_admin_id
```

Potential statuses:

```text
OPEN
UNDER_REVIEW
RESOLVED
DISMISSED
```

The exact moderation model remains to be finalized in Security/Admin design.

---

# 14. Admin Domain

## 14.1 `admin_audit_logs`

Recommended if MVP admin performs sensitive actions.

Columns:

```text
id
admin_user_id
action
target_type
target_id
metadata
created_at
```

Purpose:

Track privileged actions such as:

- suspending a user
- deleting/erasing an account
- resolving a report
- changing account status

For sensitive administrative operations, an audit trail is strongly recommended.

---

# 15. Relationship Overview

Conceptual ER structure:

```text
users
 ├── 1:1 profiles
 ├── 1:N otps
 ├── 1:N refresh_tokens
 ├── N:M languages          via user_languages
 ├── N:M interests          via user_interests
 ├── N:M users              via friendships
 ├── N:M users              via user_blocks
 ├── N:M conversations      via conversation_participants
 ├── 1:N messages           as sender
 ├── 1:N voice_calls        as caller/callee
 ├── 1:N call_feedback
 └── 1:N user_reports
```

---

# 16. Recommended MVP Table Sequence

Do not create every table immediately.

Create in dependency order.

## Existing / Auth foundation

```text
users
otps
refresh_tokens
```

## Profile feature

```text
profiles
interests
user_interests
```

## Language feature

```text
languages
user_languages
```

## Friendship

```text
friend_requests
friendships
user_blocks
```

## Messaging

```text
conversations
conversation_participants
messages
```

## Voice calling

```text
voice_calls
call_feedback
```

## Admin/moderation

```text
user_reports
admin_audit_logs
```

Only add tables when their feature is being implemented.

---

# 17. Transaction Boundaries

## Registration

```text
BEGIN
  validate uniqueness
  create user
  create verification OTP
COMMIT

dispatch email
```

If guaranteed email delivery becomes critical, use an outbox/background-job strategy rather than keeping a database transaction open during SMTP delivery.

---

## OTP verification

```text
BEGIN
  load valid OTP
  verify OTP
  mark OTP used
  activate/verify account
COMMIT
```

---

## Friend request acceptance

```text
BEGIN
  lock/read pending request
  verify block state
  verify both friend limits
  create friendship
  mark request accepted
COMMIT
```

This must be atomic to prevent exceeding friend limits through concurrent requests.

---

## Sending a message

```text
BEGIN
  validate conversation access
  validate block/interaction rules
  insert message
COMMIT

publish realtime event
```

---

## Starting a voice call

```text
BEGIN
  validate caller/callee
  validate block/call eligibility
  create RINGING call record if durable tracking is desired
COMMIT

publish signaling event
```

Call signaling state may also use Redis for short-lived coordination.

---

## Account deletion

User's current decision:

> all user data will be erased.

Therefore account deletion requires a carefully coordinated transaction/workflow.

Durable records must either:

- cascade-delete safely, or
- be explicitly removed/anonymized where legal/audit requirements require retention.

Exact policy must be finalized before implementation because moderation/audit records may conflict with complete physical deletion.

This remains an explicit open decision.

---

# 18. Concurrency and Locking

Important concurrent operations include:

- duplicate registration
- accepting friend requests
- enforcing maximum 20 friends
- message sequencing
- call state transitions
- refresh-token rotation

Use:

- unique constraints
- transactions
- row-level locking where required
- idempotency where appropriate

Do not depend only on application-level “check then insert” logic for uniqueness.

---

# 19. Indexing Strategy

Indexes should reflect query patterns.

## Users

```text
UNIQUE(username)
UNIQUE(email)
UNIQUE(phone_number)
account_status  # only if admin/query workloads justify it
```

Do not create duplicate indexes on primary keys.

## OTP

```text
(user_id, purpose, is_used)
expires_at
```

## Refresh tokens

```text
UNIQUE(token identifier/hash)
(user_id, is_revoked)
expires_at
```

## Profiles

Indexes only for fields actively used in search/filtering.

Possible later:

```text
location
profession
```

Do not index every text field.

## User interests

```text
(user_id, interest_id)
interest_id
```

## User languages

```text
user_id
(language_id, relationship_type, proficiency_level)
```

## Friendships

```text
user_low_id
user_high_id
```

## Blocks

```text
blocker_user_id
blocked_user_id
```

## Messages

```text
(conversation_id, sent_at DESC)
sent_at
```

## Calls

```text
(caller_user_id, created_at DESC)
(callee_user_id, created_at DESC)
```

---

# 20. Pagination

Never return unbounded tables.

Use pagination for:

- matching results
- friends
- conversations
- messages
- call history
- admin user/report lists

For MVP, offset/limit pagination is acceptable for smaller datasets.

For high-volume ordered data such as messages, cursor-based pagination is preferable.

Exact API representation belongs in `API_ARCHITECTURE.md`.

---

# 21. Timestamps and Timezones

All durable timestamps should use UTC-aware timestamps.

Application/UI converts to user-local time when needed.

Avoid mixing:

```text
naive datetime
timezone-aware datetime
```

Recommended PostgreSQL representation:

```text
TIMESTAMPTZ
```

Standard timestamp fields:

```text
created_at
updated_at
```

Use additional event timestamps only when semantically meaningful.

---

# 22. IDs

For the current project, integer/bigint primary keys are acceptable.

Recommended MVP:

```text
BIGINT generated identity
```

UUIDs are not required merely for architecture style.

If public resource IDs should not expose sequential IDs, this can be addressed later through UUID/public identifiers without forcing every internal table to use UUID immediately.

---

# 23. Soft Delete vs Hard Delete

Current product decision says:

> On account deletion, all user data is erased.

Therefore default user deletion direction is hard deletion/cascade removal.

However:

- admin audit records
- abuse reports
- security records
- legal/compliance needs

may require limited retained/anonymized records.

Because this conflicts with absolute deletion, final retention rules must be decided before account deletion is implemented.

Do not silently assume either behavior.

---

# 24. Message Retention

Current agreed rule:

```text
Message history = 1 week
```

Implementation should include a scheduled cleanup process.

Example:

```text
DELETE FROM messages
WHERE sent_at < now() - interval '7 days';
```

Actual cleanup should be performed safely in batches if data grows.

Related conversation rows should be cleaned only when they no longer have business value.

---

# 25. Data for Matching

Do not create a permanent `matches` table for MVP unless a real requirement needs historical recommendations.

MVP matching can be calculated from:

```text
profiles
user_interests
user_languages
friendships
user_blocks
presence (optional)
```

and return up to 20 ranked candidates.

Redis may later cache results.

This avoids unnecessary stale matching data.

---

# 26. Redis Data Architecture

Examples only; final key design belongs in Realtime Architecture.

```text
presence:user:{user_id}
ws:user:{user_id}:connections
rate_limit:auth:{identifier}
call:{call_id}:state
call:{call_id}:participants
```

Redis data should have TTLs wherever state is temporary.

Important:

```text
Redis outage ≠ loss of durable business history
```

PostgreSQL remains durable truth.

---

# 27. Alembic Migration Rules

1. Every schema change must have an Alembic migration.
2. Never edit an already-applied production migration.
3. Add a new migration to correct previous mistakes.
4. Migrations should have meaningful revision messages.
5. Upgrade and downgrade should be tested where practical.
6. CI should eventually run migrations against a test PostgreSQL database.
7. Model definitions and migrations must remain consistent.
8. Review autogenerated migrations before applying them.

---

# 28. Current Auth Database Migration Plan

Recommended corrective migrations rather than rewriting history:

## Migration A — auth integrity cleanup

- restore `otps.user_id ON DELETE CASCADE`
- restore OTP lookup indexes
- add refresh-token `user_id` index
- remove redundant explicit PK indexes if appropriate

## Migration B — auth naming/security evolution

Potentially:

```text
password → password_hash
otp → otp_hash
```

This migration needs coordinated application-code changes.

Do not rename blindly while the running application still expects old column names.

## Migration C — account model evolution

Add only when required:

```text
phone_number
role
account_status
```

Backfill existing users safely before adding strict NOT NULL constraints where needed.

---

# 29. Database Access Rules

Allowed:

```text
MessagingRepository → messages/conversations
FriendshipRepository → friendship-owned tables
ProfileRepository → profile-owned tables
```

Forbidden:

```text
MatchingRepository → directly modifies profiles
MessagingRepository → queries password/auth tables
AdminRepository → directly mutates every domain table
```

Cross-domain reads should use application/query contracts.

Because the MVP shares one PostgreSQL database, physical access is technically possible, but architecture rules still prohibit accidental ownership violations.

---

# 30. Repository Responsibilities

Repositories should:

- execute SQLAlchemy queries
- persist aggregates/entities
- expose domain/application-friendly methods
- use the active transaction/session

Repositories should not:

- call `commit()` independently
- send emails
- publish WebSocket events
- calculate unrelated business rules
- bypass authorization
- expose raw ORM models outside the module when avoidable

---

# 31. Testing Requirements for Database Layer

At minimum:

### Repository tests

Test:
- constraints
- expected queries
- cascade behavior
- unique rules
- indexes indirectly through query correctness/performance review

### Integration tests

Use real PostgreSQL for important DB behavior.

Do not rely exclusively on SQLite because SQLite differs from PostgreSQL in:

- constraints
- data types
- concurrency
- locking
- timezone behavior
- index behavior

Recommended approach:

```text
separate PostgreSQL test database / disposable container
```

---

# 32. Initial Scale Assumption

Current planning assumption:

```text
Initial usage ≈ 50 active users
```

Therefore:

- a single PostgreSQL instance is sufficient
- no sharding
- no read replicas
- no partitioning required initially
- no separate database per domain
- no distributed database architecture

Design for correctness and clear ownership first.

Scale architecture only when measurements justify it.

---

# 33. Future Scaling Options

Only when needed:

- connection-pool tuning
- query optimization
- Redis caching
- read replica
- message-table partitioning
- archival strategies
- specialized search
- asynchronous processing

These are not MVP requirements.

---

# 34. Database Security

Required:

- database credentials only through environment/secrets management
- no credentials committed to Git
- least-privilege database user in production
- encrypted TLS connection when hosted DB requires it
- no plaintext password storage
- no plaintext OTP storage
- sensitive tokens should preferably be hashed/identified securely
- logs must not expose secrets/tokens/password hashes
- production SQL echo/debug logging must be disabled

---

# 35. Backup and Recovery

Initial hosting may use Supabase/Neon or another managed PostgreSQL provider.

Required direction:

- scheduled backups
- ability to restore
- backup not stored only on the EC2 host
- periodic restore verification

Still open:

```text
RPO
RTO
backup frequency
backup retention
```

These will be finalized in NFR/infrastructure planning.

---

# 36. Open Database Decisions

The following must remain open until their dependent architecture/product decision is finalized:

1. Whether Auth and Profile share `users` information temporarily or are separated immediately.
2. Exact mandatory Profile columns.
3. Exact ownership of interests.
4. Exact multi-language cardinality rules.
5. Exact account-status enum.
6. Raw refresh token vs hashed token/JTI storage.
7. Message hard-delete vs tombstone behavior.
8. Exact admin report/audit retention.
9. Account deletion vs required moderation/audit retention.
10. Whether durable call history is required for every call attempt.
11. Exact call rating range/feedback fields.
12. Cursor-pagination format.
13. Database backup RPO/RTO.

---

# 37. Recommended ERD Summary

```text
users
 │
 ├── profiles
 │     └── user_interests ── interests
 │
 ├── user_languages ── languages
 │
 ├── otps
 ├── refresh_tokens
 │
 ├── friend_requests
 ├── friendships
 ├── user_blocks
 │
 ├── conversation_participants ── conversations
 │                                  │
 │                                  └── messages
 │
 ├── voice_calls
 │      └── call_feedback
 │
 └── user_reports
        └── admin resolution

admins are users with ADMIN role
```

---

# 38. Next Architecture Artifact

After this document:

```text
REQUIREMENTS_BASELINE.md       ✅
DOMAIN_BOUNDARIES.md           ✅
COMPONENT_ARCHITECTURE.md      ✅
DATABASE_ARCHITECTURE.md       ✅
        ↓
API_ARCHITECTURE.md            ← NEXT
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
