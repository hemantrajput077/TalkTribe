# TalkTribe — EPIC-03 Jira Stories

**Epic:** EPIC-03 — Matching & Discovery  |  EPIC-04 — Friendship & Blocking
**Milestone:** M3 — Matching + Friendship / Blocking
**Scope:** MVP
**Priority:** Critical / High
**Status:** Ready for implementation

**Primary references:**
- `development-roadmap.md` — M3 definition and slice order
- `docs/workflows/matching.md` — Matching workflow
- `docs/workflows/friendship.md` — Friendship & Blocking workflow
- `docs/architecture/database.md` — DB table design
- `docs/architecture/domain-boundaries.md` — Cross-domain contract rules
- `jira-generation-rules.md` — Ticket format and rules

**Blocked by:**
- M2 Profile + Language (PROF-06 ProfileEligibilityService — already delivered)

---

## Epic Summary

M3 creates the compatibility discovery and safe peer-interaction layer before any realtime connection is built.

Two streams run partly in parallel:

```
Stream A — Blocking + InteractionEligibility  (priority: must be done first)
Stream B — Matching                           (depends on InteractionEligibility)
Stream C — Friendship lifecycle               (depends on Block foundation)
```

Without InteractionEligibility (BLOCK-01), neither Matching nor Friendship can safely gate peer interaction.
Without Matching (MATCH-01), no user can discover compatible partners.
Without Friendship (FRIEND-01–03), users cannot connect or manage their peer list.

---

## M3 Story Index

| Story ID  | Title                                                                 | Epic    | Priority | Blocked by               |
|-----------|-----------------------------------------------------------------------|---------|----------|--------------------------|
| BLOCK-01  | User can block and unblock a peer + InteractionEligibility contract   | EPIC-04 | Critical | AUTH-09                  |
| MATCH-01  | System can discover and rank compatible English-practice candidates   | EPIC-03 | Critical | PROF-06, BLOCK-01        |
| FRIEND-01 | User can send, view, reject, and cancel friend requests               | EPIC-04 | High     | BLOCK-01                 |
| FRIEND-02 | User can accept a friend request (concurrency-safe, 20-friend limit)  | EPIC-04 | High     | FRIEND-01, BLOCK-01      |
| FRIEND-03 | User can view their friends list and remove a friend                  | EPIC-04 | High     | FRIEND-02                |

---

---

# Story 1 — BLOCK-01

## Title

**User can block and unblock a peer — includes InteractionEligibility contract**

## Epic

`EPIC-04 — Friendship & Blocking`

## Feature ID

`BLOCK-01`

## Milestone

`M3 — Matching + Friendship / Blocking`

## Priority

Critical

## User Story

As a learner,
I want to block a user who makes me uncomfortable,
so that they are completely excluded from my matches, messages, and calls.

As the TalkTribe platform,
I need an InteractionEligibility contract,
so that Matching, Pairing, Messaging, and Calls can all check block state without importing Friendship repositories directly.

## Business Context

Blocking is the highest-priority item in M3. It is a hard safety mechanism — a blocked user must
be excluded from every interaction surface: matching results, pairing queue, messaging, and calls.

The `InteractionEligibility` internal contract is equally critical. Every other domain (Matching, Pairing,
Calls, Messaging) must be able to call `is_blocked(a, b)` without depending directly on
the Friendship domain's internals. This cross-domain safety contract must be delivered before
MATCH-01 or FRIEND-01 can be implemented.

## In Scope

- `user_blocks` database table and Alembic migration
- `POST /api/v1/friends/blocks` — authenticated user blocks a target user
  - Cancels/invalidates all pending friend requests between the pair
  - Removes existing friendship if one exists
  - Commits atomically in a single transaction
- `DELETE /api/v1/friends/blocks/{user_id}` — authenticated user unblocks a target user
  - Does NOT restore previous friendship or pending requests
- `GET /api/v1/friends/blocks` — list of users the authenticated user has blocked (own block list)
- `InteractionEligibility` internal service contract in `app/domains/friendship/` application layer:
  - `is_blocked(user_a_id, user_b_id) -> bool` — true if either direction has a block
  - `are_friends(user_a_id, user_b_id) -> bool`
  - `can_interact(user_a_id, user_b_id) -> bool` — combined eligibility check
- Self-block denied (422)
- Blocking a user who is not found returns 404
- Duplicate block returns 409

## Out of Scope

- Friend request lifecycle (FRIEND-01)
- Matching implementation (MATCH-01)
- Messaging enforcement (M7)
- Call enforcement (M6)
- Admin block/unblock (M9)

## Dependencies

```
Blocked by:
  AUTH-09 — AuthenticatedIdentity contract (DELIVERED)

Consumed by:
  MATCH-01 — uses InteractionEligibility to exclude blocked candidates
  FRIEND-01 — uses InteractionEligibility to gate friend request creation
  FRIEND-02 — checks block before accepting
  PAIR-01  — uses InteractionEligibility (M5)
  CALL-01  — uses InteractionEligibility (M6)
  MSG-01   — uses InteractionEligibility (M7)
```

## Architecture References

- `docs/architecture/domain-boundaries.md` — Cross-domain contract rules (no FK imports across domains)
- `docs/architecture/database.md` — user_blocks table definition
- `docs/workflows/friendship.md` — Sections 22–30

## Acceptance Criteria

**AC1 — Block succeeds and removes friendship + pending requests**

Given an authenticated user A and an active user B
When A calls `POST /api/v1/friends/blocks` with `{"user_id": B}`
Then a block row is created for A → B
And any pending friend requests between A and B are cancelled/invalidated
And any existing friendship between A and B is removed
And the API returns HTTP 201.

**AC2 — Block prevents interaction (InteractionEligibility)**

Given A has blocked B (or B has blocked A)
When `InteractionEligibility.is_blocked(A, B)` is called
Then it returns True in both directions.

**AC3 — Unblock removes only the block**

Given A has blocked B
When A calls `DELETE /api/v1/friends/blocks/{B}`
Then the block is removed
And no friendship or pending request is automatically restored
And the API returns HTTP 204.

**AC4 — Self-block is rejected**

Given an authenticated user A
When A tries to block themselves
Then the API returns HTTP 422.

**AC5 — Duplicate block is handled gracefully**

Given A has already blocked B
When A tries to block B again
Then the API returns HTTP 409 (no duplicate row created).

**AC6 — Unauthenticated request is rejected**

Given no access token
When block or unblock endpoint is called
Then the API returns HTTP 401.

**AC7 — Block list returns only the caller's blocks**

Given A has blocked B and C
When A calls `GET /api/v1/friends/blocks`
Then only B and C appear — no other users' block lists are visible.

## Technical Notes

- `user_blocks` needs a `UNIQUE(blocker_user_id, blocked_user_id)` constraint and a check that blocker != blocked.
- Block operation must be a single transaction: create block + cancel requests + remove friendship atomically.
- `InteractionEligibility` must be importable by Matching and Pairing without circular imports.
  Keep it in `app/domains/friendship/application/interaction_eligibility.py`.
- Return 404 for non-existent target users — do not reveal whether a user is suspended/blocked.

## API Impact

```
POST   /api/v1/friends/blocks
Body:  {"user_id": <int>}
201 Created | 401 | 404 | 409 | 422

DELETE /api/v1/friends/blocks/{user_id}
204 No Content | 401 | 404

GET    /api/v1/friends/blocks
200: [{"user_id": ..., "display_name": ..., "blocked_at": ...}]
```

## Database Impact

```sql
CREATE TABLE user_blocks (
    id               SERIAL PRIMARY KEY,
    blocker_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blocked_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CHECK (blocker_user_id != blocked_user_id),
    UNIQUE (blocker_user_id, blocked_user_id)
);

CREATE INDEX ix_user_blocks_blocker ON user_blocks(blocker_user_id);
CREATE INDEX ix_user_blocks_blocked ON user_blocks(blocked_user_id);
```

New Alembic migration required.

## Security / Authorization

- Only the authenticated user may create or remove their own blocks.
- `is_blocked` checks both directions so neither party can exploit order.
- Block list is private — only the caller's list is returned.
- Rate limit: block creation should be rate-limited (10 blocks / 10 min per user).

## Test Requirements

- Block succeeds → friendship removed, requests cancelled
- Self-block returns 422
- Duplicate block returns 409
- Unblock removes only the block row
- `is_blocked(A, B)` returns True when A blocked B AND when B blocked A
- Unauthenticated returns 401
- Block list only returns caller's blocks
- Other user cannot remove A's block

## Definition of Done

- [ ] `user_blocks` migration applied
- [ ] `POST /api/v1/friends/blocks` implemented with atomic transaction
- [ ] `DELETE /api/v1/friends/blocks/{user_id}` implemented
- [ ] `GET /api/v1/friends/blocks` implemented
- [ ] `InteractionEligibility` service implemented and importable without circular dependency
- [ ] All acceptance criteria have passing tests
- [ ] Ruff + mypy pass
- [ ] PR merged to main

---

---

# Story 2 — MATCH-01

## Title

**System can discover and rank compatible English-practice candidates**

## Epic

`EPIC-03 — Matching & Discovery`

## Feature ID

`MATCH-01`

## Milestone

`M3 — Matching + Friendship / Blocking`

## Priority

Critical

## User Story

As a learner with a completed profile,
I want to discover compatible English-practice partners,
so that I can find the right person to connect with.

## Business Context

Matching is the discovery engine of TalkTribe. Without it, users have no way to find
compatible partners — the entire peer-to-peer value chain breaks. Matching must be
rule-based (not AI), deterministic, and testable for MVP.

The result feeds both the Discover screen (static recommendations) and later the
Pairing system (which reuses the same compatibility scoring for live queue selection).

## In Scope

- `GET /api/v1/matches` endpoint — returns up to 20 ranked compatible candidates
- Requester eligibility: must be authenticated, active, verified, profile complete (via `ProfileEligibilityService`)
- Candidate hard filters (exclude if any fails):
  - candidate == requester → exclude
  - candidate account not ACTIVE → exclude
  - candidate profile not complete → exclude
  - candidate has no LEARNING language → exclude
  - block in either direction (via `InteractionEligibility.is_blocked`) → exclude
- Soft scoring (higher = better match):
  - Shared interests → primary signal
  - Profession similarity → secondary signal
  - Proficiency level proximity → modest signal
- Stable tie-breaking by user_id (deterministic output for same inputs)
- Maximum 20 results enforced server-side (client `limit` param is capped at 20)
- Safe match response: only safe public fields, never email/phone/password/auth data
- On-demand calculation — no permanent `matches` table

## Out of Scope

- AI / embedding-based matching (deferred)
- Country filter (requires normalized country field — not yet available)
- Caching (Redis cache can be added later; PostgreSQL is fine at MVP scale)
- Recommendation explanation text (optional polish, not blocking)
- Whether existing friends appear in results (open decision — include them for now)

## Dependencies

```
Blocked by:
  PROF-06 — ProfileEligibilityService (DELIVERED)
  BLOCK-01 — InteractionEligibility contract

Relates to:
  PAIR-01 — Pairing will reuse the same compatibility scoring (M5)
  PROF-03 — PeerProfileResponse/SafeProfileSummary contract used by match cards
```

## Architecture References

- `docs/workflows/matching.md` — Full matching workflow and scoring shape
- `docs/adr/ADR-012-rule-based-matching-mvp.md` — MVP matching decision
- `docs/architecture/domain-boundaries.md` — Matching uses contracts, not foreign repos

## Acceptance Criteria

**AC1 — Eligible user receives ranked match candidates**

Given an authenticated, active, verified user with a complete profile and LEARNING language
When they call `GET /api/v1/matches`
Then the API returns HTTP 200 with up to 20 candidates
And candidates with more shared interests appear before those with fewer.

**AC2 — Self is never returned**

Given any valid matching request
When matches are returned
Then the requesting user does not appear in the results.

**AC3 — Blocked candidates are excluded**

Given user A has blocked user B (or B has blocked A)
When A calls `GET /api/v1/matches`
Then user B does not appear in the results regardless of compatibility score.

**AC4 — Incomplete / inactive candidates are excluded**

Given a candidate with an incomplete profile or a non-ACTIVE account
When any user requests matches
Then that candidate never appears in results.

**AC5 — Maximum 20 is enforced**

Given more than 20 eligible candidates exist
When `GET /api/v1/matches` is called
Then at most 20 results are returned regardless of any client `limit` parameter.

**AC6 — Incomplete profile cannot use matching**

Given an authenticated user with no bio or no LEARNING language
When they call `GET /api/v1/matches`
Then the API returns HTTP 403 (PROFILE_INCOMPLETE).

**AC7 — Unauthenticated request is rejected**

Given no access token
When `GET /api/v1/matches` is called
Then the API returns HTTP 401.

**AC8 — Safe response — no private fields**

Given any valid match response
Then no candidate row contains: email, phone, password_hash, role, account_status, OTP data, or refresh tokens.

**AC9 — Empty result is not an error**

Given no eligible candidates exist for the requester
When `GET /api/v1/matches` is called
Then the API returns HTTP 200 with `{"items": [], "count": 0}`.

## Technical Notes

- Scoring: `score = interest_overlap_count * 10 + profession_match * 5 + proficiency_proximity * 3`
  (exact weights are intentionally simple — they can be tuned later without API changes).
- Candidate loading must avoid N+1: batch-load profile summaries, interests, and languages.
- Cross-domain access: use `ProfileMatchingReader` and `InteractionEligibility` contracts — not raw repositories from other domains.
- The scoring formula should live in a `MatchingEngine` or `CompatibilityScorer` class so Pairing can reuse it.

## API Impact

```
GET /api/v1/matches?limit=20
Authorization: Bearer <access_token>

Response 200:
{
  "items": [
    {
      "user_id": 123,
      "display_name": "Priya S.",
      "avatar_url": null,
      "proficiency_level": "B1",
      "shared_interests": ["Photography", "Chess"],
      "profession": "Developer",
      "compatibility_score": 82
    }
  ],
  "count": 1
}

Response 401: unauthenticated
Response 403: profile incomplete / account not allowed
```

## Database Impact

No new tables. Reads from: `profiles`, `user_interests`, `interests`, `user_languages`, `user_blocks`, `users`.
Ensure indexes on `user_interests.user_id`, `user_languages.user_id`, `user_blocks.blocker_user_id / blocked_user_id`.

## Security / Authorization

- Authenticated users only — cannot request matches for another user.
- Safe profile summary DTOs — no auth-owned fields ever serialized.
- Maximum 20 prevents using Matching as a full user enumeration tool.

## Test Requirements

- Eligible user gets 200 with ranked candidates
- More shared interests = higher rank (deterministic)
- Self excluded from results
- Blocked user excluded in both directions
- Incomplete candidate excluded
- Inactive candidate excluded
- More than 20 eligible candidates → capped at 20
- Client limit param cannot exceed 20
- Incomplete requester profile returns 403
- Unauthenticated returns 401
- Empty candidate pool returns 200 with empty list
- Response schema never contains email, phone, password fields

## Definition of Done

- [ ] `GET /api/v1/matches` endpoint implemented
- [ ] Hard filters: self, inactive, incomplete, blocked — all applied
- [ ] Scoring: interest, profession, proficiency signals
- [ ] Stable tie-breaking by user_id
- [ ] Maximum 20 enforced server-side
- [ ] Safe response schema (PeerMatchResponse)
- [ ] CompatibilityScorer/MatchingEngine is importable by Pairing without code duplication
- [ ] All acceptance criteria have passing tests
- [ ] Ruff + mypy pass
- [ ] PR merged to main

---

---

# Story 3 — FRIEND-01

## Title

**User can send, view, reject, and cancel friend requests**

## Epic

`EPIC-04 — Friendship & Blocking`

## Feature ID

`FRIEND-01`

## Milestone

`M3 — Matching + Friendship / Blocking`

## Priority

High

## User Story

As a learner,
I want to send a friend request to someone I matched with,
view my incoming and outgoing requests,
reject requests I don't want,
and cancel requests I sent by mistake,
so that I control who enters my friend list.

## Business Context

Friend requests are the entry point to the friendship lifecycle. This story covers the full
request creation and viewing workflow — everything except acceptance (FRIEND-02), which carries
its own concurrency complexity. These actions do not change the friend count, so they can be
implemented without the 20-friend transaction logic.

## In Scope

- DB migrations: `friend_requests` and `friendships` tables (friendships table created here, used by FRIEND-02)
- `POST /api/v1/friends/requests` — send a friend request
  - Validate: sender != receiver, both users active, no block (via InteractionEligibility), not already friends, no duplicate pending request, sender friend count < 20
  - Handle reverse pending: if B already sent a request to A, inform A to accept it instead
- `GET /api/v1/friends/requests?direction=incoming|outgoing&status=PENDING` — view own requests
- `POST /api/v1/friends/requests/{id}/reject` — receiver rejects a PENDING request
- `DELETE /api/v1/friends/requests/{id}` — sender cancels a PENDING request (status → CANCELLED)

## Out of Scope

- Accepting requests (FRIEND-02)
- Friends list (FRIEND-03)
- Notifications (deferred to future phase)
- Admin management of requests

## Dependencies

```
Blocked by:
  BLOCK-01 — InteractionEligibility contract (block check before sending)
  AUTH-09  — AuthenticatedIdentity

Relates to:
  FRIEND-02 — accept (unblocked by this story)
  FRIEND-03 — list/remove (unblocked by FRIEND-02)
```

## Architecture References

- `docs/workflows/friendship.md` — Sections 6–17
- `docs/architecture/database.md` — friend_requests, friendships table design

## Acceptance Criteria

**AC1 — Valid request is created**

Given authenticated user A and active user B (no existing relationship, no block)
When A calls `POST /api/v1/friends/requests` with `{"receiver_id": B}`
Then a PENDING request is created
And the API returns HTTP 201.

**AC2 — Self-request is rejected**

Given authenticated user A
When A sends a request to themselves
Then the API returns HTTP 422.

**AC3 — Duplicate pending request is rejected**

Given A already has a PENDING request to B
When A tries to send another request to B
Then the API returns HTTP 409.

**AC4 — Block prevents request creation**

Given A has blocked B (or B has blocked A)
When A tries to send a friend request to B
Then the API returns HTTP 403.

**AC5 — Already-friends check**

Given A and B are already friends
When A tries to send a request to B
Then the API returns HTTP 409.

**AC6 — Sender at 20 friends cannot send request**

Given A already has 20 friends
When A tries to send a friend request
Then the API returns HTTP 422 (FRIEND_LIMIT_REACHED).

**AC7 — Receiver can reject a pending request**

Given B has a PENDING request from A
When B calls `POST /api/v1/friends/requests/{id}/reject`
Then the request status becomes REJECTED
And no friendship is created
And the API returns HTTP 200.

**AC8 — Sender can cancel an outgoing request**

Given A has a PENDING request to B
When A calls `DELETE /api/v1/friends/requests/{id}`
Then the request status becomes CANCELLED
And the API returns HTTP 204.

**AC9 — Only relevant parties can act on a request**

Given A sent a request to B
When any other user C tries to reject or cancel it
Then the API returns HTTP 403.

**AC10 — View requests returns only the caller's requests**

Given A has 2 incoming and 1 outgoing PENDING request
When A calls `GET /api/v1/friends/requests?direction=incoming`
Then only A's 2 incoming requests are returned.

## Technical Notes

- `friend_requests` status enum: PENDING, ACCEPTED, REJECTED, CANCELLED.
- Keep cancelled requests as CANCELLED rows (for audit) — do not hard-delete.
- Unique constraint: prevent two PENDING rows for the same (sender, receiver) pair.
- Reverse pending: if B→A is PENDING, return a 409 with error code `REVERSE_REQUEST_PENDING` so the frontend can prompt A to accept the existing one.

## API Impact

```
POST   /api/v1/friends/requests
Body:  {"receiver_id": <int>}
201 Created | 401 | 403 | 409 | 422

GET    /api/v1/friends/requests?direction=incoming|outgoing&status=PENDING
200: [{"id":..., "sender_id":..., "receiver_id":..., "status":..., "created_at":...}]

POST   /api/v1/friends/requests/{id}/reject
200 | 401 | 403 | 404

DELETE /api/v1/friends/requests/{id}
204 | 401 | 403 | 404
```

## Database Impact

```sql
CREATE TABLE friend_requests (
    id            SERIAL PRIMARY KEY,
    sender_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status        VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    responded_at  TIMESTAMP WITH TIME ZONE,
    CHECK (sender_id != receiver_id)
);
CREATE UNIQUE INDEX uq_friend_requests_pending
    ON friend_requests(sender_id, receiver_id)
    WHERE status = 'PENDING';
CREATE INDEX ix_friend_requests_receiver ON friend_requests(receiver_id);

CREATE TABLE friendships (
    id           SERIAL PRIMARY KEY,
    user_low_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_high_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CHECK (user_low_id < user_high_id),
    UNIQUE (user_low_id, user_high_id)
);
CREATE INDEX ix_friendships_user_low  ON friendships(user_low_id);
CREATE INDEX ix_friendships_user_high ON friendships(user_high_id);
```

New Alembic migration required.

## Security / Authorization

- Sender must be the authenticated user — cannot send on behalf of another.
- Only receiver may reject; only sender may cancel.
- Block state checked before request creation (via `InteractionEligibility`).

## Test Requirements

- Valid request creates PENDING row (201)
- Self-request returns 422
- Duplicate pending returns 409
- Blocked user returns 403
- Already friends returns 409
- Sender at 20 friends returns 422
- Receiver can reject → status = REJECTED
- Sender can cancel → status = CANCELLED
- Unrelated user cannot reject/cancel → 403
- View requests only shows caller's own requests

## Definition of Done

- [ ] `friend_requests` and `friendships` migrations applied
- [ ] `POST /api/v1/friends/requests` with all validation implemented
- [ ] `GET /api/v1/friends/requests` with direction/status filter implemented
- [ ] `POST /api/v1/friends/requests/{id}/reject` implemented
- [ ] `DELETE /api/v1/friends/requests/{id}` (cancel) implemented
- [ ] All acceptance criteria have passing tests
- [ ] Ruff + mypy pass
- [ ] PR merged to main

---

---

# Story 4 — FRIEND-02

## Title

**User can accept a friend request (concurrency-safe, 20-friend limit)**

## Epic

`EPIC-04 — Friendship & Blocking`

## Feature ID

`FRIEND-02`

## Milestone

`M3 — Matching + Friendship / Blocking`

## Priority

High

## User Story

As a learner,
I want to accept an incoming friend request,
so that the sender and I become friends and can message or call each other.

## Business Context

Acceptance is the most critical step in the friendship lifecycle — it is the only step that
creates a friendship row and is the only step where the 20-friend limit becomes a hard constraint.
The limit must be enforced inside a single database transaction with row-level locking to prevent
concurrent acceptances from pushing a user over 20 friends. This is a concurrency-sensitive story
and requires an explicit concurrent test to verify correctness.

## In Scope

- `POST /api/v1/friends/requests/{id}/accept` — receiver accepts a PENDING request
- Full atomic transaction:
  1. Verify request exists and status is PENDING
  2. Verify caller is the receiver
  3. Verify no block exists in either direction (via InteractionEligibility)
  4. Lock + count friends for both sender and receiver
  5. If both < 20: create friendship row, mark request ACCEPTED → commit
  6. If either is at 20: return 422 FRIEND_LIMIT_REACHED, do not commit
- Friendship stored as normalized pair: `user_low_id = min(A, B)`, `user_high_id = max(A, B)`

## Out of Scope

- Friends list (FRIEND-03)
- Notifications
- Realtime event on acceptance (M4+)

## Dependencies

```
Blocked by:
  FRIEND-01 — friend_requests and friendships tables must exist
  BLOCK-01  — InteractionEligibility contract
```

## Architecture References

- `docs/workflows/friendship.md` — Sections 14–15 (acceptance + concurrency)
- `docs/adr/ADR-008-application-transaction-ownership.md` — Transaction boundaries

## Acceptance Criteria

**AC1 — Receiver accepts and friendship is created**

Given B has a PENDING request from A
And neither user has blocked the other
And both have fewer than 20 friends
When B calls `POST /api/v1/friends/requests/{id}/accept`
Then exactly one friendship row is created (normalized pair)
And the request status becomes ACCEPTED
And the API returns HTTP 200.

**AC2 — Non-receiver cannot accept**

Given a request addressed to B
When user C (not B) calls the accept endpoint
Then the API returns HTTP 403.

**AC3 — Non-pending request cannot be accepted**

Given a request with status REJECTED or CANCELLED
When accept is called
Then the API returns HTTP 409.

**AC4 — Block prevents acceptance**

Given A has blocked B since the request was sent
When B tries to accept A's request
Then the API returns HTTP 403.

**AC5 — Friend limit blocks acceptance**

Given A or B already has 20 friends
When acceptance is attempted
Then no friendship is created
And request remains PENDING
And the API returns HTTP 422 (FRIEND_LIMIT_REACHED).

**AC6 — Concurrent acceptances cannot exceed the limit**

Given user A has 19 friends
And A has two pending incoming requests from B and C
When B and C both accept simultaneously
Then exactly one acceptance succeeds (friendship created)
And the other returns 422 FRIEND_LIMIT_REACHED
And A ends up with exactly 20 friends, never 21.

## Technical Notes

- Use `SELECT ... FOR UPDATE` on the friendship count query to prevent concurrent over-count.
- Store friendship as `(min(A, B), max(A, B))` — the unique constraint prevents duplicates.
- The concurrency test (AC6) is release-critical and must be included in the test suite.
- Transaction boundary: the entire accept flow (validate + lock + create + update) must be one transaction.

## API Impact

```
POST /api/v1/friends/requests/{id}/accept
Authorization: Bearer <access_token>

200 OK: {"message": "Friend request accepted", "friendship_id": <int>}
401: unauthenticated
403: not the receiver / blocked
409: request not PENDING
422: friend limit reached
```

## Database Impact

No new tables. Uses `friend_requests` and `friendships` from FRIEND-01.
Requires `SELECT FOR UPDATE` or equivalent locking on friendship count query.

## Security / Authorization

- Only the request receiver may accept.
- Block state re-checked at acceptance time (not only at request-creation time).
- 20-friend limit is authoritative at acceptance — not at send time.

## Test Requirements

- Happy path: friendship created, request ACCEPTED
- Non-receiver returns 403
- Non-pending request returns 409
- Blocked pair returns 403
- One user at limit returns 422, no friendship created
- Concurrent acceptance test: two simultaneous accepts for same user, only one succeeds
- After acceptance, both users appear in each other's friend lists

## Definition of Done

- [ ] `POST /api/v1/friends/requests/{id}/accept` implemented with atomic transaction
- [ ] Row-level locking or equivalent concurrency protection in place
- [ ] Normalized friendship pair stored correctly
- [ ] All acceptance criteria have passing tests
- [ ] Concurrent acceptance test passes (mandatory)
- [ ] Ruff + mypy pass
- [ ] PR merged to main

---

---

# Story 5 — FRIEND-03

## Title

**User can view their friends list and remove a friend**

## Epic

`EPIC-04 — Friendship & Blocking`

## Feature ID

`FRIEND-03`

## Milestone

`M3 — Matching + Friendship / Blocking`

## Priority

High

## User Story

As a learner,
I want to see who my friends are and remove someone if I no longer want to be connected,
so that I can manage my peer relationships on TalkTribe.

## Business Context

The friends list is the social foundation of TalkTribe — it drives who a user can manually
call (online friends), and it gives users visibility into their connections. Friend removal is
mutual: when A removes B, neither is in the other's friend list. This is distinct from blocking —
removal does not prevent future interaction.

## In Scope

- `GET /api/v1/friends` — list of the authenticated user's current friends (accepted friendships)
  - Returns safe profile summary per friend: user_id, display_name, avatar_url, proficiency_level
  - Does not include pending requests, blocked users, or removed friends
- `DELETE /api/v1/friends/{user_id}` — remove a friend (mutual removal)
  - Verifies the authenticated user is one participant in the friendship
  - Removes the friendship row for both parties
  - Does NOT block the removed user
  - Does NOT delete message history

## Out of Scope

- Online/presence status in the friend list (M4 Realtime Foundation)
- Blocking (BLOCK-01)
- Manual voice call to a friend (M6)
- Notifications on removal

## Dependencies

```
Blocked by:
  FRIEND-02 — friendships table and acceptance must work first
```

## Architecture References

- `docs/workflows/friendship.md` — Sections 19–20
- `docs/workflows/friendship.md` — Section 21 (remove vs block distinction)

## Acceptance Criteria

**AC1 — Friends list returns accepted friendships**

Given A and B are friends
When A calls `GET /api/v1/friends`
Then B appears in the list with their safe profile summary.

**AC2 — Friends list excludes pending/blocked/removed**

Given A has a pending request to C and has blocked D
When A calls `GET /api/v1/friends`
Then C and D do not appear in the list.

**AC3 — Safe profile summary only**

Given any friends list response
Then each item contains only: user_id, display_name, avatar_url, proficiency_level
And never contains: email, phone, password, account_status, role.

**AC4 — Friend removal is mutual**

Given A and B are friends
When A calls `DELETE /api/v1/friends/{B}`
Then the friendship row is deleted
And B no longer appears in A's friends list
And A no longer appears in B's friends list
And the API returns HTTP 204.

**AC5 — Cannot remove a non-friend**

Given A and C are not friends
When A calls `DELETE /api/v1/friends/{C}`
Then the API returns HTTP 404.

**AC6 — Cannot remove another user's friendship**

Given B and C are friends but A is not
When A calls `DELETE /api/v1/friends/{C}` (pretending to be B)
Then the API returns HTTP 404 (no information leakage).

**AC7 — Unauthenticated request is rejected**

Given no access token
When either endpoint is called
Then the API returns HTTP 401.

## Technical Notes

- Query friendships as: `WHERE user_low_id = me OR user_high_id = me` then resolve the peer ID.
- Join with `profiles` and `user_languages` to build the safe summary per friend.
- Removal is a hard delete of the friendship row — no soft-delete needed here.
- Friend removal does not trigger block; user can send a new request afterward.

## API Impact

```
GET /api/v1/friends
Authorization: Bearer <access_token>
200: [
  {
    "user_id": 12,
    "display_name": "Aarav K.",
    "avatar_url": null,
    "proficiency_level": "B2"
  }
]
401: unauthenticated

DELETE /api/v1/friends/{user_id}
204 No Content | 401 | 404
```

## Database Impact

No new tables. Reads and deletes from `friendships` (from FRIEND-01 migration).

## Security / Authorization

- Only an active participant can view their own friends list.
- Only an active participant in a friendship can remove it.
- Return 404 (not 403) when the friendship doesn't exist — avoids leaking whether a specific friendship exists.
- Response never exposes auth-domain fields.

## Test Requirements

- Friends list returns accepted friends with safe summary
- Pending requests and blocked users are not in the list
- Response never contains email, phone, account_status
- Removal deletes friendship for both users (mutual)
- Removing a non-friend returns 404
- Unrelated user cannot remove a friendship
- After removal, re-sending a friend request is allowed (no block was set)
- Unauthenticated returns 401

## Definition of Done

- [ ] `GET /api/v1/friends` implemented with safe profile summary
- [ ] `DELETE /api/v1/friends/{user_id}` implemented with mutual removal
- [ ] All acceptance criteria have passing tests
- [ ] Ruff + mypy pass
- [ ] PR merged to main

---

## M3 Implementation Order

Following the dependency chain:

```
1. BLOCK-01  — user_blocks + InteractionEligibility contract
        ↓                    ↓
2. MATCH-01           FRIEND-01 (can run in parallel after BLOCK-01)
                             ↓
                      FRIEND-02 (accept — concurrency test required)
                             ↓
                      FRIEND-03 (list + remove)
```

## M3 Exit Criteria (from roadmap)

- [ ] Matching returns safe compatible candidates
- [ ] Maximum 20 is enforced server-side
- [ ] Self / inactive / incomplete users are excluded from matches
- [ ] Blocked users are never recommended
- [ ] Friend request lifecycle works (send, view, reject, cancel)
- [ ] Friend acceptance works with 20-friend rule enforced transactionally
- [ ] Friend list and removal work
- [ ] Blocking / unblocking works
- [ ] InteractionEligibility contract exists and is importable by other domains
- [ ] Matching and Friendship tests pass (including concurrency test for FRIEND-02)
