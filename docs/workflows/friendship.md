# TalkTribe Friendship Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** Friendship / Connection  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `TARGET_ARCHITECTURE.md`, `PROFILE_WORKFLOW.md`, `MATCHING_WORKFLOW.md`, `SECURITY_ARCHITECTURE.md`, `DATABASE_ARCHITECTURE.md`

---

# 1. Purpose

This document defines the end-to-end Friendship and Blocking workflow for TalkTribe MVP.

It covers:

- sending friend requests
- receiving requests
- accepting requests
- rejecting requests
- cancelling outgoing requests
- removing friends
- maximum friend limit
- blocking
- unblocking
- interaction eligibility
- matching integration
- messaging integration
- call integration
- security rules
- failure cases
- testing
- Definition of Done

Friendship and Blocking are related but not identical concepts.

Friendship answers:

```text
Are these users connected as friends?
```

Blocking answers:

```text
Is interaction between these users prohibited?
```

---

# 2. MVP Friendship Decision

TalkTribe supports:

```text
send friend request
accept friend request
reject friend request
cancel outgoing request
friends list
remove friend
block user
unblock user
```

Current product rule:

```text
maximum friends per user = 20
```

---

# 3. Friendship Is Not Required for All Interaction

Current product decision:

```text
Friendship is not always required before messaging.
```

Messaging depends on the recipient's messaging permission and block state.

Therefore Friendship must expose relationship information, but it must not force every communication flow to require:

```text
friendship == true
```

Possible interaction logic:

```text
blocked?
   ↓
yes → deny

not blocked
   ↓
recipient messaging preference
   ├── friends only → require friendship
   └── eligible users → friendship not required
```

Exact messaging preference model is finalized in the Messaging workflow.

---

# 4. Friendship Data Model

Recommended durable records:

```text
friend_requests
friendships
user_blocks
```

Conceptual request fields:

```text
id
sender_user_id
receiver_user_id
status
created_at
responded_at
```

Conceptual friendship fields:

```text
user_low_id
user_high_id
created_at
```

Conceptual block fields:

```text
blocker_user_id
blocked_user_id
created_at
```

---

# 5. Friend Request States

Recommended request states:

```text
PENDING
ACCEPTED
REJECTED
CANCELLED
```

Core state transitions:

```text
PENDING
  ├── ACCEPTED
  ├── REJECTED
  └── CANCELLED
```

Do not allow:

```text
ACCEPTED → PENDING
REJECTED → ACCEPTED
CANCELLED → ACCEPTED
```

without creating a new request.

---

# 6. Send Friend Request — Happy Path

```text
Authenticated User A
        ↓
Select User B
        ↓
POST /api/v1/friends/requests
        ↓
Validate:
- A != B
- both users exist
- both accounts active
- no blocking relationship
- not already friends
- no equivalent pending request
- sender friend count < 20
        ↓
Create PENDING request
        ↓
Commit
        ↓
Return request
```

---

# 7. Self-Request Prevention

A user cannot send a friend request to themselves.

```text
sender_user_id == receiver_user_id
```

→ reject.

Recommended error:

```text
FRIEND_REQUEST_TO_SELF_NOT_ALLOWED
```

---

# 8. Existing Friendship Check

Before creating a request:

```text
Are A and B already friends?
```

If yes:

```text
do not create another friend request
```

Return:

```text
ALREADY_FRIENDS
```

or an equivalent conflict result.

---

# 9. Duplicate Pending Request

If A already has a pending request to B:

```text
do not create another row
```

Return:

```text
FRIEND_REQUEST_ALREADY_PENDING
```

Database/application constraints should prevent duplicate active pending requests.

---

# 10. Reverse Pending Request

Scenario:

```text
A → B is pending
B tries to send request to A
```

Recommended behavior:

```text
do not create a second opposite request
```

Instead the UI/application should surface the existing incoming request to B so B can:

```text
accept
reject
```

This avoids duplicate relationship state.

---

# 11. Friend Limit

Current product decision:

```text
Maximum friends = 20
```

Before acceptance, both users must remain within the limit.

Important:

The friend count should be checked during the **acceptance transaction**, not only when the request is originally sent.

Why:

```text
User A has 19 friends
A sends requests to B, C, D
B accepts → A has 20
C accepts concurrently
```

Without transaction-safe checking, A could exceed the limit.

---

# 12. Send Request and Friend Limit

Recommended behavior:

A user at 20 friends:

```text
cannot send new friend requests
```

Reason:

They cannot currently complete another friendship.

However the authoritative final check still happens during acceptance.

---

# 13. Receive Friend Requests

Recommended endpoint:

```text
GET /api/v1/friends/requests
```

Possible filters:

```text
incoming
outgoing
pending
```

Example:

```text
GET /friends/requests?direction=incoming&status=PENDING
```

Only the authenticated user's relevant requests may be returned.

---

# 14. Accept Friend Request — Happy Path

```text
User B receives request from A
        ↓
POST /friends/requests/{id}/accept
        ↓
Authenticate B
        ↓
Load request
        ↓
Verify:
- request exists
- B is receiver
- status = PENDING
- both users active
- no block relationship
        ↓
BEGIN TRANSACTION
        ↓
Check friend count for A
        ↓
Check friend count for B
        ↓
If both < 20
        ↓
Create friendship
        ↓
Mark request ACCEPTED
        ↓
COMMIT
        ↓
Return success
```

---

# 15. Concurrent Acceptance

Friend-limit enforcement must be safe under concurrency.

Possible implementation strategies:

```text
row-level lock
transactional count + lock
advisory lock
other database-safe concurrency technique
```

Choose the simplest reliable implementation.

The invariant is:

```text
friend count must never exceed 20
```

---

# 16. Reject Friend Request

```text
User B
   ↓
POST /friends/requests/{id}/reject
   ↓
Verify B is receiver
   ↓
Verify request PENDING
   ↓
Set REJECTED
   ↓
Commit
```

After rejection:

```text
no friendship is created
```

---

# 17. Cancel Outgoing Request

Sender may cancel a pending outgoing request.

```text
User A
   ↓
DELETE /friends/requests/{id}
   ↓
Verify A is sender
   ↓
Verify PENDING
   ↓
Set CANCELLED or remove according to persistence policy
```

Recommended:

```text
retain state as CANCELLED
```

if request history is useful.

Hard deletion is also possible if history is not needed.

Choose one consistent strategy.

---

# 18. Re-Sending After Rejection or Cancellation

Current exact product rule is not fully finalized.

Recommended MVP direction:

```text
allow a new request later
```

provided:

```text
not blocked
not already friends
friend limit allows
cooldown/abuse rules allow
```

A rejected/cancelled historical request should not permanently prevent future friendship.

---

# 19. Friends List

Recommended endpoint:

```text
GET /api/v1/friends
```

Response may include safe summary:

```text
user_id
display_name
profile_photo
proficiency
online_status if allowed
```

Do not return private account fields.

---

# 20. Friend Removal

```text
Authenticated User A
        ↓
DELETE /api/v1/friends/{friend_user_id}
        ↓
Verify friendship exists
        ↓
Verify A is one participant
        ↓
Remove friendship
        ↓
Commit
```

Friend removal is mutual relationship removal.

After removal:

```text
A is no longer B's friend
B is no longer A's friend
```

---

# 21. Remove Friend vs Block

These must remain separate.

## Remove Friend

```text
friendship removed
future interaction may still be possible
new friend request may be possible
messaging may still be possible depending preferences
```

## Block

```text
peer interaction prohibited
matching excluded
friend requests prohibited
messages prohibited
calls prohibited
```

---

# 22. Blocking — Happy Path

```text
User A
   ↓
POST /api/v1/friends/blocks
   ↓
target = User B
   ↓
Validate:
- A != B
- B exists
   ↓
BEGIN TRANSACTION
   ↓
Create block A → B
   ↓
Remove/cancel relevant pending friend requests
   ↓
Apply friendship behavior if required
   ↓
COMMIT
```

Current product decision:

```text
blocked user can do nothing toward blocker
```

---

# 23. Blocking Direction

Blocking is directional.

```text
A blocks B
```

means at minimum:

```text
B cannot interact with A
```

For simplicity and safety, TalkTribe interaction eligibility should usually treat a block in **either direction** as prohibiting peer interaction between the pair.

Thus:

```text
A blocked B
OR
B blocked A
```

→ Messaging/Calling/Matching between them is denied.

---

# 24. Blocking and Existing Friendship

The exact product choice was not separately finalized, but the safest MVP workflow is:

```text
block
   ↓
remove existing friendship
```

Reason:

Keeping a "friendship" active while all interaction is prohibited creates confusing state.

This should be confirmed during implementation planning if the product wants a different behavior.

If this rule changes, update this workflow/ADR rather than silently changing code.

---

# 25. Blocking and Pending Requests

When A blocks B:

```text
pending A → B request
pending B → A request
```

should no longer remain actionable.

Recommended:

```text
cancel/invalidate pending requests
```

---

# 26. Blocking and Existing Conversation

Current product decision:

```text
existing conversation remains
new message exchange is disabled
```

Therefore:

```text
conversation history → retained according to message retention policy
message.send → denied
```

Messaging must call Friendship/Block eligibility before sending.

---

# 27. Blocking and Matching

A blocked pair must never be recommended.

```text
Matching
   ↓
InteractionEligibility
   ↓
blocked in either direction?
   ├── yes → exclude
   └── no → continue
```

---

# 28. Blocking and Pairing

Automatic pairing must exclude blocked users.

Even if:

```text
high compatibility
both online
both waiting
```

block state always wins.

```text
blocked = hard exclusion
```

---

# 29. Blocking and Voice Calls

Manual or automatic voice calls must be denied when blocked.

```text
call.start
   ↓
InteractionEligibility
   ↓
blocked?
   ├── yes → CALL_NOT_ALLOWED
   └── no → continue
```

---

# 30. Unblock Workflow

```text
User A
   ↓
DELETE /api/v1/friends/blocks/{user_id}
   ↓
Verify A created the block
   ↓
Remove block
   ↓
Commit
```

Unblocking does not automatically restore:

```text
friendship
pending friend request
conversation permission preference
```

Users may reconnect normally afterward if allowed.

---

# 31. Interaction Eligibility Contract

Friendship should expose a contract such as:

```text
InteractionEligibility
```

Conceptual methods:

```text
is_blocked(user_a, user_b)
are_friends(user_a, user_b)
can_send_friend_request(user_a, user_b)
```

Potential higher-level method:

```text
can_interact(user_a, user_b, interaction_type)
```

Do not force all domains to import Friendship repositories.

---

# 32. Cross-Domain Usage

## Matching

Needs:

```text
block exclusion
friend/request state if shown in recommendations
```

## Messaging

Needs:

```text
block state
friendship state when messaging preference requires it
```

## Pairing

Needs:

```text
block exclusion
interaction eligibility
```

## Calls

Needs:

```text
block exclusion
friendship state for manual-friend-call rules if required
```

---

# 33. Manual Friend Call Rule

The current product concept says:

```text
users should be able to manually call friends who are online
```

Therefore manual friend call should require:

```text
friendship
+
not blocked
+
target online/available
```

Automatic pairing does not require friendship.

This distinction is important.

---

# 34. Friend Request Notifications

Notifications are deferred until after core peer-to-peer functionality.

Therefore MVP friend request workflow should work without push/email notification infrastructure.

The frontend can retrieve/display pending requests through API/realtime UI when available.

Future Notification domain may consume:

```text
FriendRequestCreated
FriendRequestAccepted
```

events.

---

# 35. Abuse Prevention

Friend requests can be abused.

At minimum:

```text
rate limit request creation
prevent duplicates
respect blocks
cap friends
```

Potential future controls:

```text
request cooldown after repeated rejection
spam detection
admin moderation
```

Do not add complex abuse systems before observed need.

---

# 36. API Surface

Recommended:

```text
GET    /api/v1/friends
POST   /api/v1/friends/requests
GET    /api/v1/friends/requests
POST   /api/v1/friends/requests/{id}/accept
POST   /api/v1/friends/requests/{id}/reject
DELETE /api/v1/friends/requests/{id}
DELETE /api/v1/friends/{user_id}

POST   /api/v1/friends/blocks
DELETE /api/v1/friends/blocks/{user_id}
```

Optional:

```text
GET /api/v1/friends/blocks
```

for a user's own blocked-user management screen.

---

# 37. Error Codes

Recommended:

```text
FRIEND_REQUEST_TO_SELF_NOT_ALLOWED
FRIEND_REQUEST_ALREADY_PENDING
FRIEND_REQUEST_NOT_FOUND
FRIEND_REQUEST_NOT_PENDING
FRIEND_REQUEST_ACTION_NOT_ALLOWED
ALREADY_FRIENDS
NOT_FRIENDS
FRIEND_LIMIT_REACHED
USER_BLOCKED
BLOCK_ALREADY_EXISTS
BLOCK_NOT_FOUND
INTERACTION_NOT_ALLOWED
```

---

# 38. Authorization Rules

Normal user may:

```text
send request as themselves
view own incoming/outgoing requests
accept own incoming request
reject own incoming request
cancel own outgoing request
remove own friendship
create own block
remove own block
```

Normal user may not:

```text
accept request addressed to someone else
cancel another user's request
remove friendship between two other users
create block on behalf of someone else
read arbitrary users' friend-request histories
```

---

# 39. Transaction Boundaries

## Accept request

```text
BEGIN
  validate request
  verify no block
  lock/check counts
  create friendship
  update request
COMMIT
```

## Block

```text
BEGIN
  create block
  cancel pending requests
  remove friendship if approved rule
COMMIT
```

## Remove friend

```text
BEGIN
  delete friendship
COMMIT
```

Repositories should not commit independently.

---

# 40. Database Constraints

Recommended:

## Friend request

```text
sender != receiver
```

Prevent duplicate active pending request per pair.

## Friendship

Normalized pair:

```text
user_low_id < user_high_id
UNIQUE(user_low_id, user_high_id)
```

## Block

```text
blocker != blocked
UNIQUE(blocker_user_id, blocked_user_id)
```

Database constraints complement application validation.

---

# 41. Frontend Friend Request Flow

```text
Matching / Profile page
        ↓
Add Friend
        ↓
POST friend request
        ↓
Success
        ↓
UI state:
Request Pending
```

Receiver:

```text
Friend Requests screen
        ↓
Incoming request
        ↓
Accept / Reject
```

---

# 42. Frontend Block Flow

```text
Profile / Conversation
        ↓
Block User
        ↓
Confirmation
        ↓
POST block
        ↓
Interaction disabled
```

Unblock:

```text
Settings / Blocked Users
        ↓
Unblock
```

---

# 43. Failure Scenarios

## Target user deleted/inactive

```text
request denied
```

## Block exists

```text
request/message/call/match interaction denied
```

## Friend limit reached before acceptance

```text
accept fails
FRIEND_LIMIT_REACHED
```

Request may remain pending or transition according to implementation/product choice.

Recommended:

```text
remain pending
```

until the user can make space, unless a timeout/expiry policy is introduced.

## Concurrent duplicate request

Database constraint ensures only one valid pending relationship.

---

# 44. Friend Request Expiration

No explicit expiration requirement is currently defined.

MVP can leave pending requests until:

```text
accepted
rejected
cancelled
blocked
account removed
```

Future expiration may be introduced if stale requests become a UX problem.

---

# 45. Friend Count

Friend count shown on profile should be derived from accepted friendships.

Do not count:

```text
pending requests
rejected requests
blocked users
```

---

# 46. Testing Workflow

## Send Request

- valid request succeeds
- self request denied
- duplicate pending denied
- reverse pending handled
- already-friends denied
- blocked user denied
- sender at 20 friends denied

## Accept

- receiver accepts successfully
- sender cannot accept own outgoing request
- unrelated user denied
- non-pending request denied
- block created before acceptance causes denial
- friend limit checked for both users
- concurrent acceptance cannot exceed limit

## Reject/Cancel

- receiver can reject
- sender can cancel
- unauthorized user denied

## Remove

- friend can remove relationship
- unrelated user cannot manipulate relationship

## Block

- block succeeds
- self block denied
- duplicate block handled
- pending requests invalidated
- interaction eligibility becomes false
- matching excludes blocked pair
- messaging denied
- call denied

## Unblock

- blocker can unblock
- other user cannot remove block
- friendship not automatically restored

---

# 47. Definition of Done — Friendship

Friendship/Blocking is ready when:

- [ ] User can send a friend request.
- [ ] Self requests are denied.
- [ ] Duplicate/reverse pending requests are handled.
- [ ] User can view own friend requests.
- [ ] Receiver can accept.
- [ ] Receiver can reject.
- [ ] Sender can cancel.
- [ ] Accepted friendship is stored once for both users.
- [ ] User can list friends.
- [ ] User can remove a friend.
- [ ] Maximum 20 friends is enforced transactionally.
- [ ] User can block another user.
- [ ] User can unblock another user.
- [ ] Block in either direction prevents peer interaction.
- [ ] Blocked users are excluded from Matching.
- [ ] Blocked users cannot message each other.
- [ ] Blocked users cannot call each other.
- [ ] Existing conversation history is not automatically erased by blocking.
- [ ] Cross-domain access uses an eligibility contract.
- [ ] Authorization tests pass.
- [ ] Concurrency tests protect the friend limit.

---

# 48. Open Friendship Decisions

Still to finalize:

1. Whether blocking automatically removes an existing friendship — recommended yes.
2. Whether accepted/rejected/cancelled request history is retained forever.
3. Whether a cooldown applies after rejection.
4. Whether pending requests expire.
5. Whether existing friends appear in Matching recommendations.
6. Whether pending-request users appear in Matching recommendations.
7. Whether the receiver may configure who can send friend requests.
8. Exact behavior if friend limit is reached after a request was already sent.
9. Whether basic profile visibility remains after block.

These should be decided explicitly before code depends on them.

---

# 49. Friendship Workflow Diagram

```text
                      USER A
                        │
                        ▼
                  VIEW USER B
                        │
                        ▼
                SEND FRIEND REQUEST
                        │
                        ▼
                     PENDING
               ┌────────┼─────────┐
               │        │         │
               ▼        ▼         ▼
            ACCEPT    REJECT    CANCEL
               │
               ▼
      CHECK BOTH FRIEND LIMITS
               │
               ▼
           FRIENDSHIP
               │
          ┌────┴────┐
          │         │
          ▼         ▼
       REMOVE      BLOCK
                      │
                      ▼
               INTERACTION DENIED
             ┌────────┼────────┐
             ▼        ▼        ▼
          MATCHING  MESSAGE   CALL
          EXCLUDED   DENIED   DENIED
```

---

# 50. Next Workflow

```text
AUTHENTICATION_WORKFLOW.md      ✅
PROFILE_WORKFLOW.md             ✅
LANGUAGE_WORKFLOW.md            ✅
MATCHING_WORKFLOW.md            ✅
FRIENDSHIP_WORKFLOW.md          ✅
        ↓
PRESENCE_WORKFLOW.md            ← NEXT
        ↓
PAIRING_WORKFLOW.md
        ↓
VOICE_CALL_WORKFLOW.md
        ↓
MESSAGING_WORKFLOW.md
        ↓
FEEDBACK_REPORTING_WORKFLOW.md
        ↓
ADMIN_WORKFLOW.md
        ↓
FEATURE_DEPENDENCIES.md
        ↓
DEVELOPMENT_ROADMAP.md
        ↓
JIRA
```
