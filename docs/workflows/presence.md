# TalkTribe Presence Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** Presence  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `TARGET_ARCHITECTURE.md`, `REALTIME_ARCHITECTURE.md`, `SECURITY_ARCHITECTURE.md`, `AUTHENTICATION_WORKFLOW.md`, `FRIENDSHIP_WORKFLOW.md`

---

# 1. Purpose

This document defines the end-to-end Presence workflow for TalkTribe MVP.

It covers:

- when a user is considered online
- WebSocket connection lifecycle
- authenticated presence
- multi-device / multi-tab behavior
- heartbeat
- stale connection cleanup
- Redis storage
- online/offline events
- presence visibility
- presence integration with Friendship
- presence integration with Matching/Pairing
- presence integration with Messaging
- presence integration with Voice Calls
- reconnect behavior
- failure cases
- testing
- Definition of Done

Presence answers:

```text
Is this user currently active in TalkTribe?
```

It does not own:

```text
friendship
matching score
message persistence
call authorization
profile data
```

---

# 2. MVP Presence Decision

Current product decision:

```text
User is online when actively using the application.
User becomes offline when they stop using it.
```

Presence should be realtime.

No detailed last-seen feature is required for MVP.

---

# 3. Presence Goals

The Presence system must:

1. identify active authenticated users
2. support multiple tabs/devices
3. avoid falsely leaving users online forever
4. recover from abnormal disconnects
5. provide online/offline state to approved consumers
6. support live pairing
7. support manual friend calls
8. work across multiple backend instances later
9. avoid storing live presence as durable PostgreSQL truth

---

# 4. Presence Entry Point

Presence begins when the frontend establishes an authenticated WebSocket connection.

Flow:

```text
User logs in
   ↓
Frontend opens WebSocket
   ↓
Backend authenticates connection
   ↓
Connection registered
   ↓
Presence updated
   ↓
User becomes online
```

---

# 5. Authentication Requirement

Only authenticated active users can establish a normal presence connection.

Validate:

```text
access token valid
user exists
account verified
account ACTIVE
```

If not:

```text
WebSocket rejected
presence not created
```

---

# 6. Server-Side Identity

The server must derive identity from the authenticated WebSocket session.

Do not trust:

```text
client-supplied user_id
```

as proof of identity.

Presence is bound to:

```text
AuthenticatedIdentity.user_id
```

---

# 7. Connection Registration

When a socket is accepted:

```text
create connection_id
        ↓
associate:
connection_id → user_id
        ↓
register local connection
        ↓
update Redis connection state
```

Conceptually:

```text
User 123
 ├── conn_A
 ├── conn_B
 └── conn_C
```

---

# 8. Multi-Device / Multi-Tab Rule

A user is online if:

```text
active_connection_count > 0
```

Therefore:

```text
tab 1 connected
tab 2 connected
```

and tab 1 closes:

```text
user still online
```

Only when the final active connection is gone:

```text
user becomes offline
```

---

# 9. Online Transition

Transition:

```text
0 active connections
   ↓
1 active connection
```

causes:

```text
OFFLINE → ONLINE
```

Presence system may publish:

```text
presence.online
```

to authorized subscribers.

---

# 10. Additional Connection

Transition:

```text
1 active connection
   ↓
2 active connections
```

does **not** create another logical online transition.

The user was already online.

This avoids duplicate presence events.

---

# 11. Disconnect Workflow

Normal disconnect:

```text
WebSocket closes
   ↓
unregister connection
   ↓
decrement/remove connection from Redis
   ↓
connections remaining?
   ├── Yes → user remains online
   └── No  → user becomes offline
```

---

# 12. Abnormal Disconnect

A browser or network may disappear without a clean WebSocket close.

Examples:

```text
Wi-Fi lost
browser crash
device sleep
network change
```

Presence must not rely only on explicit disconnect events.

Use:

```text
heartbeat
+
TTL
```

to detect stale connections.

---

# 13. Heartbeat Workflow

Conceptual flow:

```text
Client
   ↓ heartbeat/ping
Backend
   ↓ update liveness timestamp
Redis
   ↓ refresh TTL
```

If heartbeats continue:

```text
connection remains active
```

If they stop:

```text
TTL expires
   ↓
connection considered stale
   ↓
cleanup
```

---

# 14. Heartbeat Interval

Exact interval remains configurable.

Example operational direction:

```text
heartbeat every ~20–30 seconds
```

with a larger expiry window.

Do not hardcode architecture around one permanent value.

The important rule is:

```text
heartbeat interval < presence TTL
```

---

# 15. Presence TTL

Each temporary connection/presence record should expire automatically if not refreshed.

Example concept:

```text
connection TTL = 60–90 seconds
```

Exact value is an implementation configuration.

TTL prevents stale online users after unexpected disconnects.

---

# 16. Redis Presence Storage

Possible conceptual keys:

```text
presence:user:{user_id}
connections:user:{user_id}
connection:{connection_id}
```

Possible values:

```text
ONLINE
connection IDs
last heartbeat timestamp
```

Exact Redis data structure is implementation-specific.

Recommended choices may include:

```text
SET
HASH
SORTED SET
```

depending on cleanup/query needs.

---

# 17. Redis Is Not Durable Presence History

Do not store live presence state in PostgreSQL for every connect/disconnect.

PostgreSQL may later store:

```text
last_seen_at
```

if a future requirement needs it.

For MVP:

```text
Redis = operational presence source
```

---

# 18. Presence Query

Other modules should use a Presence contract.

Example:

```text
PresenceReader
```

Conceptual methods:

```text
is_online(user_id)
get_online_status(user_ids)
is_available_for_call(user_id)
```

Do not let other modules access Redis keys directly.

---

# 19. Presence Visibility

Presence is not automatically public to every authenticated user.

Likely approved consumers:

```text
friends list
conversation participants
call target
matching/pairing internals
```

The frontend should not receive a global list of all online users unless explicitly approved.

---

# 20. Friend Presence

Friends list may show:

```text
online
offline
```

Flow:

```text
GET /friends
   ↓
friend summaries
   ↓
PresenceReader batch lookup
   ↓
online status added
```

or presence updates may arrive over WebSocket.

---

# 21. Friend Presence Subscription

When a user's friend becomes online/offline:

```text
Presence publishes state change
   ↓
Realtime layer identifies relevant friends
   ↓
presence.online / presence.offline
   ↓
friend UI updates
```

Do not broadcast to unrelated users.

---

# 22. Presence and Messaging

Messaging can use presence to decide:

```text
deliver realtime now?
```

If recipient online:

```text
persist message
   ↓
send WebSocket event
```

If offline:

```text
persist message
   ↓
no realtime delivery
   ↓
recipient retrieves later
```

Presence must not determine whether a message is allowed.

Messaging permission still depends on:

```text
blocking
conversation access
messaging preference
```

---

# 23. Presence and Matching

Discovery matching does not require users to be online.

Therefore:

```text
GET /matches
```

may include offline candidates.

Presence should not become a hard dependency for ordinary discovery.

---

# 24. Presence and Pairing

Live pairing requires current availability.

Before entering pairing:

```text
authenticated socket active?
        ↓
user online?
        ↓
user available for pairing?
```

If WebSocket disconnects and grace period/TTL expires:

```text
remove user from pairing queue
```

---

# 25. Presence vs Availability

These are different concepts.

## Online

```text
User has active TalkTribe connection.
```

## Available for pairing/call

```text
User is online
AND
not already in call
AND
not in conflicting state
AND
actively opted into pairing where required
```

Therefore:

```text
online != automatically available
```

---

# 26. Call Availability

Manual friend call should check:

```text
target online?
target already in call?
target available for incoming call?
not blocked?
friendship valid?
```

Presence supplies only the live connection/availability part.

Calls/Friendship own the rest.

---

# 27. Active Call Presence

A user in an active call is still:

```text
ONLINE
```

but may be:

```text
UNAVAILABLE_FOR_NEW_CALL
```

This call availability state may be derived through Calls + Presence.

Do not represent all of this as a single online/offline boolean.

---

# 28. Pairing Availability State

Possible transient states:

```text
ONLINE_IDLE
PAIRING_WAITING
PAIRING_RESERVED
RINGING
IN_CALL
```

These should not necessarily become a giant Presence state machine.

Recommended ownership:

```text
Presence → online/offline
Pairing → waiting/reserved
Calls → ringing/in-call
```

A higher-level availability query can combine them.

---

# 29. Reconnect Workflow

If WebSocket disconnects:

```text
frontend retries
   ↓
new WebSocket authenticated
   ↓
new connection registered
   ↓
user remains/returns online
```

Use exponential backoff with jitter client-side.

---

# 30. Reconnect Grace

For a brief network interruption:

```text
old connection disappears
new connection appears shortly after
```

the system should avoid unnecessary user-facing flapping if possible.

Possible strategy:

```text
TTL naturally provides a short grace window
```

No complex custom grace mechanism is required initially unless UX testing shows a problem.

---

# 31. Multiple Backend Instances

Initial deployment may run one backend instance.

Future:

```text
User A → Backend 1
User B → Backend 2
```

Presence must still work.

Redis provides shared state.

Local `ConnectionManager` only knows local sockets.

Redis provides:

```text
global user presence
cross-instance coordination
```

---

# 32. Presence Events

Recommended client-facing events:

```text
presence.online
presence.offline
```

Potential internal events:

```text
presence.connection_added
presence.connection_removed
presence.user_online
presence.user_offline
```

Do not expose internal connection details to clients unnecessarily.

---

# 33. Event Example

```json
{
  "type": "presence.online",
  "version": 1,
  "data": {
    "user_id": 123
  }
}
```

Only send this event to clients authorized to receive that user's presence state.

---

# 34. Client Startup Workflow

After login:

```text
Frontend loads app
        ↓
open WebSocket
        ↓
authenticate
        ↓
connection accepted
        ↓
presence online
        ↓
load:
- profile
- friends
- conversations
- other required data
```

If WebSocket fails:

```text
REST features may still work
realtime features show degraded/unavailable state
```

---

# 35. Logout Workflow

On normal logout:

```text
revoke session/refresh token
        ↓
close WebSocket
        ↓
remove connection
        ↓
last connection?
   ├── no → remain online from another session
   └── yes → offline
```

Logout-all should ultimately invalidate all authenticated sessions.

Existing active sockets should be closed or rejected on future authorization checks according to session strategy.

---

# 36. Suspended / Blocked Account

If admin suspends or platform-blocks a user:

```text
account status changed
        ↓
refresh tokens revoked
        ↓
active WebSocket should be disconnected
        ↓
presence removed
        ↓
user offline
```

This prevents suspended users from remaining active through an existing socket.

---

# 37. Presence and User Blocking

User A blocking User B does not mean:

```text
B is globally offline
```

It only affects whether presence is visible/useful to that pair.

Presence is global operational state.

Friendship/authorization determines who may consume it.

---

# 38. Privacy Behavior After Block

If A blocks B:

```text
B should not receive actionable presence information about A
```

because B cannot interact with A.

Exact profile-status rendering can be finalized with block privacy rules.

---

# 39. Failure: Redis Unavailable

If Redis is unavailable:

```text
presence state cannot be trusted globally
```

Recommended behavior:

- do not claim definitive online presence
- disable/degrade pairing
- manual calls may be temporarily unavailable
- durable REST features may continue
- messages remain safe in PostgreSQL

Do not silently return stale online values.

---

# 40. Failure: WebSocket Unavailable

If client cannot establish WebSocket:

```text
user should not be considered realtime-online
```

They may still use non-realtime REST features.

Voice calling/pairing should be unavailable until realtime connection exists.

---

# 41. Failure: Duplicate Connection Cleanup

If stale and new connections both appear:

```text
connection-specific IDs
+
TTL
```

prevent the old session from keeping the user online forever.

Do not model only:

```text
presence:user = true/false
```

without accounting for multiple connections.

---

# 42. Rate Limits

WebSocket connection attempts may be rate-limited to prevent abuse.

Heartbeat events should be lightweight.

Clients should not be able to flood arbitrary presence updates.

The client should **not** send:

```text
"I am online"
"I am offline"
```

as authoritative business state.

The backend derives presence from connection lifecycle.

---

# 43. Logging

Safe presence logs:

```text
user_id
connection_id
connected
disconnected
heartbeat timeout
presence transition
backend instance
request/correlation ID
```

Do not log access tokens.

Avoid excessive logging of every heartbeat in production unless troubleshooting.

---

# 44. Metrics

Useful metrics:

```text
active WebSocket connections
online users
average connections per user
stale connections cleaned
WebSocket reconnect rate
Redis presence errors
```

These are useful later for operations and scaling.

---

# 45. API / Realtime Boundary

Presence is primarily realtime.

A small REST endpoint may exist if useful:

```text
GET /api/v1/presence/{user_id}
```

but only if product/API needs it.

Preferred UI behavior:

```text
initial state via existing resource response/batch query
updates via WebSocket
```

Do not create large presence REST APIs without need.

---

# 46. Cross-Domain Contract Example

Conceptual:

```python
class PresenceReader(Protocol):
    async def is_online(self, user_id: int) -> bool:
        ...

    async def get_online_users(self, user_ids: list[int]) -> set[int]:
        ...
```

Calls may need a higher-level availability contract, but the exact interface should remain small.

---

# 47. Testing Workflow

## Authentication

- valid authenticated socket connects
- invalid token rejected
- unverified user rejected
- suspended user rejected

## Single Connection

- first connection marks user online
- disconnect marks user offline

## Multiple Connections

- first connection → online
- second connection → still online
- one disconnect → still online
- final disconnect → offline

## Heartbeat

- heartbeat refreshes TTL
- stale connection expires
- stale final connection causes offline transition

## Reconnect

- reconnect creates new connection safely
- stale old connection does not keep user permanently online

## Friendship Integration

- friend can receive permitted presence update
- unrelated user does not receive unauthorized broadcast
- blocked user does not receive actionable presence event

## Pairing

- offline user cannot join live pairing
- disconnect removes stale waiting user after expiry

## Calls

- offline friend cannot receive manual live call
- online eligible friend can proceed to call workflow

## Redis Failure

- presence reports degraded/unavailable rather than fabricated state

---

# 48. Definition of Done — Presence

Presence is ready when:

- [ ] Authenticated WebSocket connection is implemented.
- [ ] Server binds socket to trusted authenticated user identity.
- [ ] ConnectionManager supports multiple connections per user.
- [ ] First connection changes user to online.
- [ ] Final connection removal changes user to offline.
- [ ] Heartbeat/liveness mechanism exists.
- [ ] Redis TTL prevents stale presence.
- [ ] Redis stores shared transient presence state.
- [ ] Presence survives architecture transition to multiple backend instances.
- [ ] Friends can receive permitted online/offline state.
- [ ] Presence is not globally broadcast to all users.
- [ ] Matching discovery does not unnecessarily require online state.
- [ ] Pairing requires active presence.
- [ ] Calls can query realtime availability.
- [ ] Messaging can use presence for realtime delivery without making it durable truth.
- [ ] Suspended users are removed from active realtime presence.
- [ ] Redis failure degrades safely.
- [ ] Automated presence tests pass.

---

# 49. Open Presence Decisions

Still to finalize:

1. Exact WebSocket URL.
2. Exact WebSocket handshake authentication method.
3. Heartbeat interval.
4. Presence TTL.
5. Whether online status appears on all authenticated profiles or only selected contexts.
6. Whether any `last_seen_at` feature is added later.
7. Exact reconnect/backoff values.
8. Whether app background/minimized state remains ONLINE.
9. Exact availability aggregation interface between Presence, Pairing, and Calls.
10. Whether REST presence lookup is needed.

These should be finalized during implementation planning rather than guessed in code.

---

# 50. Presence Workflow Diagram

```text
                     USER LOGGED IN
                           │
                           ▼
                  OPEN WEBSOCKET
                           │
                           ▼
                     AUTHENTICATE
                           │
                           ▼
                  REGISTER CONNECTION
                           │
                           ▼
                 CONNECTION COUNT > 0
                           │
                           ▼
                         ONLINE
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
          FRIENDS       MESSAGING      PAIRING
        status view     live delivery  availability
                                         │
                                         ▼
                                       CALLS
                           │
                           ▼
                       HEARTBEAT
                           │
                 refresh Redis TTL
                           │
                 ┌─────────┴─────────┐
                 │                   │
            still alive          timeout/disconnect
                 │                   │
                 ▼                   ▼
               ONLINE        remove connection
                                     │
                            connections remaining?
                               ┌─────┴─────┐
                               │           │
                              yes          no
                               │           │
                               ▼           ▼
                            ONLINE       OFFLINE
```

---

# 51. Next Workflow

```text
AUTHENTICATION_WORKFLOW.md      ✅
PROFILE_WORKFLOW.md             ✅
LANGUAGE_WORKFLOW.md            ✅
MATCHING_WORKFLOW.md            ✅
FRIENDSHIP_WORKFLOW.md          ✅
PRESENCE_WORKFLOW.md            ✅
        ↓
PAIRING_WORKFLOW.md             ← NEXT
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
