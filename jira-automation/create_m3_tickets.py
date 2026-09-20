"""
Create all M3 — Matching + Friendship / Blocking tickets on JIRA.

Epics created:
  EPIC-03 — Matching & Discovery
  EPIC-04 — Friendship & Blocking

Stories created (in dependency order):
  BLOCK-01  User can block and unblock a peer + InteractionEligibility contract
  MATCH-01  System can discover and rank compatible English-practice candidates
  FRIEND-01 User can send, view, reject, and cancel friend requests
  FRIEND-02 User can accept a friend request (concurrency-safe, 20-friend limit)
  FRIEND-03 User can view their friends list and remove a friend

Source:  docs/planning/epic-03-jira-stories.md
Run:     python create_m3_tickets.py
"""

from jira_client import JiraClient

# ── Epic definitions ──────────────────────────────────────────────────────────

EPICS = [
    {
        "key": "matching",
        "summary": "EPIC-03 — Matching & Discovery",
        "labels": ["backend", "matching", "mvp", "m3"],
        "description": (
            "M3 Matching Epic.\n\n"
            "Implements the rule-based compatibility discovery engine. "
            "Allows learners to find compatible English-practice partners "
            "based on shared interests, profession, and proficiency. "
            "Returns at most 20 safe, ranked candidates. "
            "Depends on ProfileEligibilityService (PROF-06) and InteractionEligibility (BLOCK-01).\n\n"
            "Milestone: M3 — Matching + Friendship / Blocking\n"
            "Workflow: docs/workflows/matching.md\n"
            "ADR: ADR-012-rule-based-matching-mvp.md"
        ),
    },
    {
        "key": "friendship",
        "summary": "EPIC-04 — Friendship & Blocking",
        "labels": ["backend", "friendship", "blocking", "mvp", "m3"],
        "description": (
            "M3 Friendship & Blocking Epic.\n\n"
            "Implements the full peer relationship layer: blocking, friend requests, "
            "acceptance, friend list, and removal. "
            "Also delivers the InteractionEligibility internal contract consumed by "
            "Matching, Pairing, Calls, and Messaging to check block state.\n\n"
            "Milestone: M3 — Matching + Friendship / Blocking\n"
            "Workflow: docs/workflows/friendship.md"
        ),
    },
]

# ── Story definitions ─────────────────────────────────────────────────────────

STORIES = [
    # ── BLOCK-01 ──────────────────────────────────────────────────────────────
    {
        "epic_key": "friendship",
        "feature_id": "BLOCK-01",
        "priority": "critical",
        "labels": ["backend", "blocking", "security", "database", "mvp", "m3"],
        "summary": "User can block/unblock a peer + InteractionEligibility contract",
        "description": """\
Feature ID: BLOCK-01
Milestone: M3
Blocked by: AUTH-09 (DELIVERED)
Consumed by: MATCH-01, FRIEND-01, FRIEND-02, PAIR-01 (M5), CALL-01 (M6), MSG-01 (M7)

USER STORY
As a learner, I want to block a user who makes me uncomfortable so they are excluded from my matches, messages, and calls.
As the TalkTribe platform, I need an InteractionEligibility contract so all domains can check block state without importing Friendship internals.

BUSINESS CONTEXT
Blocking is the highest-priority item in M3 and must be delivered first. The InteractionEligibility internal contract is the cross-domain safety interface that Matching, Pairing, Calls, and Messaging will all depend on.

IN SCOPE
- user_blocks table + Alembic migration
- POST /api/v1/friends/blocks — block a user (atomic: cancel pending requests + remove friendship)
- DELETE /api/v1/friends/blocks/{user_id} — unblock (does NOT restore friendship)
- GET /api/v1/friends/blocks — caller's own block list
- InteractionEligibility internal service: is_blocked(a, b), are_friends(a, b), can_interact(a, b)
  Lives in: app/domains/friendship/application/interaction_eligibility.py
- Self-block → 422, duplicate block → 409, target not found → 404

OUT OF SCOPE: Friend request lifecycle (FRIEND-01), Matching (MATCH-01), Messaging (M7), Admin block (M9)

ACCEPTANCE CRITERIA
AC1 — Block succeeds, friendship removed, pending requests cancelled, returns 201
AC2 — InteractionEligibility.is_blocked(A, B) returns True in both directions when either user has blocked the other
AC3 — Unblock removes only the block row; no friendship/request is restored; returns 204
AC4 — Self-block returns 422
AC5 — Duplicate block returns 409 (no second row created)
AC6 — Unauthenticated request returns 401
AC7 — GET /friends/blocks only returns the caller's own blocks

API IMPACT
POST   /api/v1/friends/blocks          Body: {"user_id": int}  → 201 | 401 | 404 | 409 | 422
DELETE /api/v1/friends/blocks/{user_id}                        → 204 | 401 | 404
GET    /api/v1/friends/blocks                                  → 200 list

DATABASE IMPACT
CREATE TABLE user_blocks (
  id SERIAL PK, blocker_user_id INT FK users(id), blocked_user_id INT FK users(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  CHECK(blocker != blocked), UNIQUE(blocker_user_id, blocked_user_id)
);
Indexes on both FK columns. New Alembic migration required.

SECURITY
- Only authenticated user may create/remove own blocks
- is_blocked checks both directions
- Rate limit: 10 blocks per 10 min per user

TEST REQUIREMENTS
- Block → friendship removed, requests cancelled
- Self-block → 422 | Duplicate block → 409
- Unblock removes only block row
- is_blocked symmetric in both directions
- Unauthenticated → 401
- Block list private to caller
- Another user cannot remove someone else's block\
""",
    },

    # ── MATCH-01 ──────────────────────────────────────────────────────────────
    {
        "epic_key": "matching",
        "feature_id": "MATCH-01",
        "priority": "critical",
        "labels": ["backend", "matching", "database", "security", "mvp", "m3"],
        "summary": "System can discover and rank compatible English-practice candidates",
        "description": """\
Feature ID: MATCH-01
Milestone: M3
Blocked by: PROF-06 (DELIVERED), BLOCK-01 (InteractionEligibility)
Relates to: PAIR-01 (M5) — Pairing will reuse CompatibilityScorer

USER STORY
As a learner with a completed profile, I want to discover compatible English-practice partners so I can find the right person to connect with.

BUSINESS CONTEXT
Matching is the discovery engine of TalkTribe. Without it users have no way to find partners. It must be rule-based (not AI), deterministic, and testable for MVP. The same scoring logic will be reused by Pairing (M5).

IN SCOPE
- GET /api/v1/matches endpoint — returns up to 20 ranked candidates
- Requester eligibility: authenticated, active, verified, profile complete (ProfileEligibilityService)
- Hard filters (exclude if any fails): self, inactive account, incomplete profile, no LEARNING language, blocked in either direction (InteractionEligibility.is_blocked)
- Soft scoring: shared interests (primary), profession match (secondary), proficiency proximity (modest)
- Stable tie-breaking by user_id (deterministic)
- Maximum 20 enforced server-side regardless of client limit param
- Safe response: user_id, display_name, avatar_url, proficiency_level, shared_interests, profession, compatibility_score — NO email/phone/password/auth fields
- On-demand calculation — no permanent matches table
- CompatibilityScorer class importable by Pairing without code duplication

OUT OF SCOPE: AI matching, country filter, Redis caching, recommendation explanation text, friends excluded from results (open decision — include them for now)

ACCEPTANCE CRITERIA
AC1 — Eligible user gets 200 with ranked candidates; more shared interests = higher rank
AC2 — Requesting user never appears in their own results
AC3 — Blocked candidate excluded in both directions (A blocked B OR B blocked A)
AC4 — Incomplete / inactive candidates excluded
AC5 — Maximum 20 enforced; client cannot bypass with limit param
AC6 — Incomplete requester profile returns 403 (PROFILE_INCOMPLETE)
AC7 — Unauthenticated returns 401
AC8 — Response never contains email, phone, password_hash, role, account_status
AC9 — No eligible candidates → 200 with {"items": [], "count": 0}

SCORING SHAPE (adjust weights during implementation)
score = interest_overlap * 10 + profession_match * 5 + proficiency_proximity * 3

API IMPACT
GET /api/v1/matches?limit=20  →  200 {"items": [...], "count": N} | 401 | 403
Each item: {user_id, display_name, avatar_url, proficiency_level, shared_interests[], profession, compatibility_score}

DATABASE IMPACT
No new tables. Reads: profiles, user_interests, interests, user_languages, user_blocks, users.
Verify indexes: user_interests.user_id, user_languages.user_id, user_blocks.blocker/blocked_user_id.

SECURITY
- Authenticated users only — cannot request matches for another user
- Safe DTO serialization — no auth-owned fields ever included
- Max 20 prevents using Matching as a full user enumeration tool

TEST REQUIREMENTS
- Eligible user gets ranked results (more shared interests = higher rank)
- Self excluded | Blocked excluded both directions | Inactive/incomplete excluded
- More than 20 eligible candidates → capped at 20
- Client limit param cannot exceed 20
- Incomplete requester → 403 | Unauthenticated → 401
- Empty pool → 200 empty list
- Response schema never contains private fields
- CompatibilityScorer importable by Pairing\
""",
    },

    # ── FRIEND-01 ─────────────────────────────────────────────────────────────
    {
        "epic_key": "friendship",
        "feature_id": "FRIEND-01",
        "priority": "high",
        "labels": ["backend", "friendship", "database", "mvp", "m3"],
        "summary": "User can send, view, reject, and cancel friend requests",
        "description": """\
Feature ID: FRIEND-01
Milestone: M3
Blocked by: BLOCK-01 (InteractionEligibility), AUTH-09 (DELIVERED)
Unblocks: FRIEND-02 (accept), FRIEND-03 (list/remove)

USER STORY
As a learner, I want to send a friend request to someone I matched with, view my incoming and outgoing requests, reject requests I don't want, and cancel requests I sent by mistake — so that I control who enters my friend list.

BUSINESS CONTEXT
Friend requests are the entry point to the friendship lifecycle. This story covers everything except acceptance (FRIEND-02), which carries its own concurrency complexity. These actions do not change the friend count.

IN SCOPE
- DB migrations: friend_requests table + friendships table (used by FRIEND-02)
- POST /api/v1/friends/requests — send a friend request
  Validates: sender != receiver, both active, no block (InteractionEligibility), not already friends, no duplicate pending, sender friend count < 20
  Handles reverse pending: if B→A already pending, return 409 REVERSE_REQUEST_PENDING
- GET /api/v1/friends/requests?direction=incoming|outgoing&status=PENDING — view own requests
- POST /api/v1/friends/requests/{id}/reject — receiver rejects a PENDING request
- DELETE /api/v1/friends/requests/{id} — sender cancels (status → CANCELLED, row retained)

OUT OF SCOPE: Accepting requests (FRIEND-02), friends list (FRIEND-03), notifications (future)

ACCEPTANCE CRITERIA
AC1 — Valid request creates PENDING row, returns 201
AC2 — Self-request returns 422
AC3 — Duplicate pending request returns 409
AC4 — Block in either direction returns 403
AC5 — Already friends returns 409
AC6 — Sender at 20 friends returns 422 (FRIEND_LIMIT_REACHED)
AC7 — Receiver can reject → status REJECTED, no friendship created, returns 200
AC8 — Sender can cancel → status CANCELLED, returns 204
AC9 — Unrelated user cannot reject/cancel → 403
AC10 — View requests only returns caller's own requests

API IMPACT
POST   /api/v1/friends/requests                  Body: {"receiver_id": int}  → 201 | 401 | 403 | 409 | 422
GET    /api/v1/friends/requests?direction=&status=                           → 200 list
POST   /api/v1/friends/requests/{id}/reject                                 → 200 | 401 | 403 | 404
DELETE /api/v1/friends/requests/{id}                                        → 204 | 401 | 403 | 404

DATABASE IMPACT
CREATE TABLE friend_requests (
  id SERIAL PK, sender_id INT FK, receiver_id INT FK, status VARCHAR(20) DEFAULT 'PENDING',
  created_at TIMESTAMPTZ, responded_at TIMESTAMPTZ, CHECK(sender != receiver)
);
UNIQUE INDEX on (sender_id, receiver_id) WHERE status = 'PENDING';
CREATE TABLE friendships (
  id SERIAL PK, user_low_id INT FK, user_high_id INT FK, created_at TIMESTAMPTZ,
  CHECK(user_low_id < user_high_id), UNIQUE(user_low_id, user_high_id)
);
New Alembic migration required.

SECURITY
- Sender must be the authenticated user
- Only receiver may reject; only sender may cancel
- Block checked via InteractionEligibility before creation

TEST REQUIREMENTS
- Valid request → 201 | Self → 422 | Duplicate pending → 409
- Blocked user → 403 | Already friends → 409 | Sender at limit → 422
- Receiver rejects → REJECTED | Sender cancels → CANCELLED
- Unrelated user cannot act on request → 403
- View returns only caller's own requests\
""",
    },

    # ── FRIEND-02 ─────────────────────────────────────────────────────────────
    {
        "epic_key": "friendship",
        "feature_id": "FRIEND-02",
        "priority": "high",
        "labels": ["backend", "friendship", "database", "security", "concurrency", "mvp", "m3"],
        "summary": "User can accept a friend request — concurrency-safe, 20-friend limit enforced",
        "description": """\
Feature ID: FRIEND-02
Milestone: M3
Blocked by: FRIEND-01 (tables), BLOCK-01 (InteractionEligibility)

USER STORY
As a learner, I want to accept an incoming friend request so that the sender and I become friends and can message or call each other.

BUSINESS CONTEXT
Acceptance is the most critical step in the friendship lifecycle — the only step that creates a friendship row and the only place where the 20-friend limit is a hard constraint. The limit must be enforced inside a single database transaction with row-level locking. The concurrent acceptance test is release-critical.

IN SCOPE
- POST /api/v1/friends/requests/{id}/accept
- Full atomic transaction:
  1. Verify request exists and status == PENDING
  2. Verify caller is the receiver
  3. Verify no block in either direction (InteractionEligibility)
  4. SELECT FOR UPDATE on friendship count for both users
  5. If both < 20: create friendship (normalized pair), mark request ACCEPTED, commit
  6. If either >= 20: return 422 FRIEND_LIMIT_REACHED, do not commit
- Friendship stored as: user_low_id = min(A,B), user_high_id = max(A,B)

OUT OF SCOPE: Friends list (FRIEND-03), notifications, realtime event on acceptance (M4+)

ACCEPTANCE CRITERIA
AC1 — Receiver accepts; friendship created; request → ACCEPTED; returns 200
AC2 — Non-receiver trying to accept returns 403
AC3 — Non-PENDING request returns 409
AC4 — Block created after request was sent → acceptance returns 403
AC5 — Either user at 20 friends → 422 FRIEND_LIMIT_REACHED; request stays PENDING; no friendship created
AC6 — CONCURRENCY TEST (MANDATORY): A has 19 friends, two concurrent acceptances from B and C → exactly one succeeds, one gets 422; A ends with exactly 20 friends, never 21

API IMPACT
POST /api/v1/friends/requests/{id}/accept  →  200 | 401 | 403 | 409 | 422
200 body: {"message": "Friend request accepted", "friendship_id": int}

DATABASE IMPACT
No new tables. Uses friend_requests and friendships from FRIEND-01.
Requires SELECT FOR UPDATE or equivalent on friendship count query.

SECURITY
- Only receiver may accept
- Block re-checked at acceptance time (not only at request creation)
- 20-friend limit is authoritative at acceptance, not at send time

TEST REQUIREMENTS
- Happy path: friendship created, request ACCEPTED, returns 200
- Non-receiver → 403 | Non-pending → 409 | Blocked pair → 403
- One user at 20 → 422, no friendship created
- CONCURRENT TEST: two simultaneous accepts for same user, only one succeeds (mandatory)\
""",
    },

    # ── FRIEND-03 ─────────────────────────────────────────────────────────────
    {
        "epic_key": "friendship",
        "feature_id": "FRIEND-03",
        "priority": "high",
        "labels": ["backend", "friendship", "mvp", "m3"],
        "summary": "User can view their friends list and remove a friend",
        "description": """\
Feature ID: FRIEND-03
Milestone: M3
Blocked by: FRIEND-02 (friendships table populated by acceptance)

USER STORY
As a learner, I want to see who my friends are and remove someone if I no longer want to be connected, so that I can manage my peer relationships.

BUSINESS CONTEXT
The friends list drives who a user can manually call (online friends in M6) and gives users visibility into their connections. Friend removal is mutual and distinct from blocking — removal does not prevent future interaction.

IN SCOPE
- GET /api/v1/friends — list authenticated user's friends (accepted friendships only)
  Safe profile summary per friend: user_id, display_name, avatar_url, proficiency_level
  Does NOT include pending requests, blocked users, or removed friends
- DELETE /api/v1/friends/{user_id} — mutual friend removal
  Verifies caller is a participant; deletes the friendship row for both parties
  Does NOT block the removed user; does NOT delete message history

OUT OF SCOPE: Online/presence status (M4), blocking (BLOCK-01), manual call to friend (M6), notifications on removal

ACCEPTANCE CRITERIA
AC1 — Friends list returns all accepted friendships with safe summary; returns 200
AC2 — Pending requests, blocked users, and removed users are not in the list
AC3 — Response never contains email, phone, password_hash, role, or account_status
AC4 — Removing a friend is mutual: both users no longer see each other in their lists; returns 204
AC5 — Removing a non-friend returns 404
AC6 — Unrelated user cannot remove another pair's friendship → 404 (no information leakage)
AC7 — Unauthenticated request returns 401
AC8 — After removal (no block), re-sending a friend request is allowed

API IMPACT
GET    /api/v1/friends  →  200 [{user_id, display_name, avatar_url, proficiency_level}] | 401
DELETE /api/v1/friends/{user_id}  →  204 | 401 | 404

DATABASE IMPACT
No new tables. Reads and hard-deletes from friendships (FRIEND-01 migration).
Query: WHERE user_low_id = me OR user_high_id = me, then resolve peer ID.
Join profiles + user_languages for the safe summary.

SECURITY
- Only a participant can view their own friend list or remove a friendship
- Return 404 (not 403) for non-existent friendship — avoid leaking relationship existence
- Response never exposes auth-domain fields

TEST REQUIREMENTS
- Friends list returns accepted friends with safe summary
- Pending/blocked users not in list
- Response schema clean of private fields
- Removal is mutual for both users
- Remove non-friend → 404
- Unrelated user cannot remove a friendship → 404
- After removal, new friend request is possible (no block set)
- Unauthenticated → 401\
""",
    },
]


# ── Runner ────────────────────────────────────────────────────────────────────

def main():
    client = JiraClient()

    # Verify connection
    me = client.get_myself()
    print(f"\nConnected as: {me.get('displayName')} ({me.get('emailAddress')})")
    print(f"Project: {client.get_project().get('name')}\n")
    print("=" * 65)
    print("  Creating M3 — Matching + Friendship / Blocking Tickets")
    print("=" * 65)

    # Step 1: Create Epics and capture their Jira keys
    print("\n[1/2] Creating Epics...")
    epic_keys = {}
    for epic_def in EPICS:
        result = client.create_epic(
            summary=epic_def["summary"],
            description=epic_def["description"],
            labels=epic_def["labels"],
        )
        epic_keys[epic_def["key"]] = result["key"]

    print(f"\n  Epic map: {epic_keys}")

    # Step 2: Create Stories linked to their Epics
    print("\n[2/2] Creating Stories...")
    story_results = []
    for story in STORIES:
        epic_jira_key = epic_keys.get(story["epic_key"])
        result = client.create_story(
            summary=story["summary"],
            description=story["description"],
            epic_key=epic_jira_key,
            priority=story["priority"],
            labels=story["labels"],
            feature_id=story["feature_id"],
        )
        story_results.append({
            "feature_id": story["feature_id"],
            "key": result["key"],
            "summary": story["summary"],
        })

    # Summary
    jira_base = client.base_url.replace("/rest/api/3", "")
    print("\n" + "=" * 65)
    print("  DONE — M3 Tickets Created")
    print("=" * 65)

    print("\n  Epics:")
    for k, v in epic_keys.items():
        print(f"    {v}  {k}  ->  {jira_base}/browse/{v}")

    print("\n  Stories:")
    for r in story_results:
        print(f"    {r['key']}  [{r['feature_id']}]  {r['summary'][:55]}...")
        print(f"           {jira_base}/browse/{r['key']}")


if __name__ == "__main__":
    main()
