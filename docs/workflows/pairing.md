# TalkTribe Pairing Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** Pairing / Live Connection  
**Depends on:** `MATCHING_WORKFLOW.md`, `PRESENCE_WORKFLOW.md`, `FRIENDSHIP_WORKFLOW.md`, `PROFILE_WORKFLOW.md`, `LANGUAGE_WORKFLOW.md`, `REALTIME_ARCHITECTURE.md`

---

# 1. Purpose

This document defines the end-to-end automatic co-learner pairing workflow for TalkTribe MVP.

Pairing answers:

```text
Which compatible learner should this user connect with right now?
```

It combines:

```text
matching compatibility
+
realtime presence
+
availability
+
interaction eligibility
+
waiting queue state
```

Matching and Pairing must remain separate.

---

# 2. MVP Pairing Goal

The core product flow is:

```text
User wants to talk
   ↓
Join waiting pool
   ↓
Find another eligible learner who also wants to talk
   ↓
Choose a compatible peer
   ↓
Reserve both users
   ↓
Create call context
   ↓
Begin voice connection
```

Automatic pairing does not require users to already be friends.

---

# 3. Pairing Preconditions

Before a user may enter the pairing pool:

```text
authenticated
verified
account ACTIVE
profile complete
English language setup valid
WebSocket connected
online
not already in an active/ringing call
not already reserved for another pairing
```

Optional future preconditions may include conversation preferences.

---

# 4. Join Pairing Flow

```text
User selects "Find someone to talk to"
        ↓
pairing.join
        ↓
Authenticate socket identity
        ↓
Validate account state
        ↓
Validate profile completion
        ↓
Validate English-practice eligibility
        ↓
Validate not already in call
        ↓
Validate not already waiting/reserved
        ↓
Create/refresh queue entry
        ↓
Attempt candidate selection
```

---

# 5. Waiting Pool

Redis is the temporary waiting store.

Conceptual key:

```text
pairing:queue:english
```

Queue entry may include:

```text
user_id
joined_at
matching bucket/reference
connection_id/session reference
```

Do not store unnecessary sensitive profile data in Redis.

---

# 6. Matching Inputs

Pairing must reuse the Matching domain's compatibility rules.

Possible inputs:

```text
shared interests
profession
proficiency
English eligibility
```

Pairing adds realtime constraints:

```text
currently waiting
online
available
not reserved
not in call
```

---

# 7. Candidate Hard Filters

Candidate must:

```text
not be requester
be ACTIVE
be verified
have complete profile
be English-practice eligible
be online
be in pairing queue
not be in active/ringing call
not be reserved elsewhere
not be blocked in either direction
be interaction-eligible
```

Any failed hard condition removes the candidate.

---

# 8. Candidate Ranking

After hard filtering:

```text
calculate compatibility
   ↓
rank candidates
   ↓
select best eligible available candidate
```

The exact scoring weights remain owned by Matching.

Pairing must not create a second independent matching formula.

---

# 9. Atomic Reservation

The most important concurrency rule:

```text
one user cannot be paired with two people
```

Example race:

```text
A waiting
B waiting
C waiting

Worker 1 → pair A + B
Worker 2 → pair B + C
```

This must never succeed.

Use an atomic Redis operation, transaction, Lua script, or equivalent safe mechanism.

---

# 10. Successful Pairing

```text
A + B selected
        ↓
atomically reserve A and B
        ↓
remove both from waiting queue
        ↓
create pairing/call context
        ↓
persist call metadata if required
        ↓
pairing.matched → A
pairing.matched → B
        ↓
voice-call workflow begins
```

---

# 11. Pairing Response

Example realtime event:

```json
{
  "type": "pairing.matched",
  "data": {
    "call_id": 123,
    "peer": {
      "user_id": 456,
      "display_name": "Partner",
      "profile_photo_url": null,
      "proficiency_level": "B1",
      "shared_interests": ["Photography", "Chess"]
    }
  }
}
```

Return only a safe peer summary.

---

# 12. Pairing Waiting State

If no suitable candidate exists:

```text
user remains waiting
```

Client receives:

```text
pairing.waiting
```

The user may:

```text
continue waiting
cancel
disconnect
```

---

# 13. Cancel Pairing

```text
pairing.leave
   ↓
validate authenticated requester
   ↓
remove queue entry
   ↓
release reservation if still safely cancellable
   ↓
pairing.cancelled
```

A user already in an accepted/active call should follow Call cancellation/end rules instead.

---

# 14. Disconnect While Waiting

If the user's WebSocket disconnects:

```text
temporary disconnect
   ↓
presence TTL/grace
```

If connection does not recover:

```text
remove user from pairing queue
release temporary reservation
```

Stale users must not remain pairable.

---

# 15. Queue TTL

Queue entries should have timeout/TTL behavior.

This protects against:

```text
browser crash
network loss
backend restart
stale waiting state
```

Exact TTL is configurable.

---

# 16. Pairing Timeout

The exact user-facing wait timeout is not finalized.

Architecture must support:

```text
still searching
cancel
no partner found
retry
```

Do not pair with an ineligible user merely because the wait is long.

---

# 17. Repeated Pairing

After a completed call:

```text
User can choose "Find another learner"
```

Flow restarts:

```text
validate availability
join queue
find new candidate
```

Future rule may avoid immediate rematching with the same person.

That rule is not yet finalized.

---

# 18. Blocking During Wait

If A blocks B while both are waiting:

```text
block state becomes authoritative immediately
```

They must not be paired.

Eligibility should be revalidated immediately before final reservation.

---

# 19. Account State Change During Wait

If admin suspends a waiting user:

```text
session disconnected
queue entry removed
reservation released
```

Pairing must not continue from stale account state.

---

# 20. Presence Integration

Presence provides:

```text
is_online
active connection
```

Pairing owns:

```text
waiting
reserved
```

Calls own:

```text
ringing
active
```

Do not merge these into one giant state machine.

---

# 21. Calls Integration

After pairing:

```text
pairing result
   ↓
Call Application
   ↓
call state created
   ↓
signaling begins
```

Pairing stops owning the interaction once call lifecycle begins.

---

# 22. Redis Failure

If Redis is unavailable:

```text
automatic pairing unavailable
```

The system should return a clear realtime/service-unavailable state.

Do not attempt unsafe in-memory matching if multiple instances or state consistency cannot be guaranteed.

---

# 23. PostgreSQL Failure

If durable call creation is required and PostgreSQL fails:

```text
do not report pairing success
```

Release reservations safely.

---

# 24. Pairing Events

Recommended:

```text
pairing.join
pairing.waiting
pairing.matched
pairing.leave
pairing.cancelled
pairing.failed
```

Optional:

```text
pairing.searching
```

---

# 25. Pairing Error Codes

Recommended:

```text
PROFILE_INCOMPLETE
LANGUAGE_PROFILE_INCOMPLETE
PAIRING_NOT_ALLOWED
PAIRING_ALREADY_WAITING
PAIRING_ALREADY_RESERVED
USER_ALREADY_IN_CALL
REALTIME_CONNECTION_REQUIRED
PAIRING_SERVICE_UNAVAILABLE
NO_COMPATIBLE_PEER
```

---

# 26. Rate Limiting

Protect:

```text
pairing.join
pairing.leave
```

against rapid abuse.

Repeated joins should not create duplicate queue records.

---

# 27. Idempotency

`pairing.leave` should be safe if repeated.

`pairing.join` should not create duplicate active queue entries.

Use server-side state to keep operations stable under retries.

---

# 28. Frontend Flow

```text
Home
  ↓
Talk Now
  ↓
Searching...
  ↓
Matched?
 ├── Yes → show peer → voice connection
 └── No  → keep waiting / cancel
```

---

# 29. Testing

- eligible user joins
- incomplete profile rejected
- offline/no socket rejected
- blocked users never paired
- incompatible users not chosen
- highest valid compatible candidate selected
- user cannot be double-paired
- two workers cannot reserve same user
- disconnect removes stale waiting user
- cancel removes queue entry
- suspended user removed
- Redis failure degrades safely
- pairing hands off correctly to Call domain

---

# 30. Definition of Done — Pairing

- [ ] Eligible user can enter waiting pool.
- [ ] Ineligible users are rejected.
- [ ] Matching compatibility is reused.
- [ ] Blocked users are excluded.
- [ ] Presence is required.
- [ ] One user cannot be reserved twice.
- [ ] Queue state is stored transiently in Redis.
- [ ] Stale entries expire.
- [ ] User can cancel.
- [ ] Successful match removes both users from queue.
- [ ] Safe peer summary is returned.
- [ ] Pairing hands off to Call workflow.
- [ ] Redis/PostgreSQL failures are handled safely.
- [ ] Automated concurrency tests pass.

---

# 31. Open Decisions

1. Exact queue data structure.
2. Exact wait timeout.
3. Exact tie-breaker.
4. Recently matched-user exclusion.
5. Whether pairing starts ringing or directly begins mutual call connection.
6. Exact reconnect grace.
7. Whether compatibility threshold is required.
8. Whether users may choose "random" instead of best compatible peer.

---

# 32. Workflow Diagram

```text
USER WANTS TO TALK
        ↓
PAIRING.JOIN
        ↓
VALIDATE ACCOUNT / PROFILE / LANGUAGE
        ↓
ONLINE + AVAILABLE?
        ↓
ADD TO REDIS WAITING POOL
        ↓
LOAD WAITING CANDIDATES
        ↓
BLOCK / ELIGIBILITY FILTERS
        ↓
MATCHING SCORE
        ↓
ATOMIC RESERVATION
        ↓
REMOVE BOTH FROM QUEUE
        ↓
CREATE CALL CONTEXT
        ↓
PAIRING.MATCHED
        ↓
VOICE_CALL_WORKFLOW
```
