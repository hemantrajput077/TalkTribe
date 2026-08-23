# TalkTribe Realtime Architecture

**Status:** Stage 2 architecture design  
**Architecture style:** Modular Monolith  
**Realtime transport:** WebSocket  
**Voice media:** WebRTC  
**Realtime coordination:** Redis  
**Durable data:** PostgreSQL  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `DOMAIN_BOUNDARIES.md`, `COMPONENT_ARCHITECTURE.md`, `DATABASE_ARCHITECTURE.md`, `API_ARCHITECTURE.md`, `SECURITY_ARCHITECTURE.md`

---

# 1. Purpose

This document defines the realtime architecture for TalkTribe MVP.

It covers:

- authenticated WebSocket connections
- connection lifecycle
- online/offline presence
- Redis Pub/Sub
- chat delivery
- typing indicators
- read receipts
- automatic co-learner pairing
- manual friend-to-friend calling
- voice-call signaling
- WebRTC offer/answer/ICE exchange
- STUN/TURN usage
- call lifecycle
- reconnection
- multiple devices
- horizontal scaling
- event authorization
- failure handling
- realtime testing

The realtime layer is transport and coordination infrastructure. Business rules stay in the appropriate domains.

---

# 2. Realtime Goals

TalkTribe's core MVP experience is:

```text
Authenticate
   ↓
Complete profile
   ↓
Become available
   ↓
Find / match with compatible co-learner
   ↓
Connect
   ↓
Talk through voice
   ↓
Rate / report
   ↓
Connect again
```

The system also supports:

```text
Friend is online
   ↓
User manually calls friend
   ↓
Friend accepts
   ↓
WebRTC voice connection
```

Realtime architecture must support both flows.

---

# 3. Core Realtime Components

```text
React Client
   │
   ├── REST
   │
   ├── WebSocket
   │
   └── WebRTC
   │
   ▼
FastAPI
   │
   ├── WebSocket Transport
   │
   ├── Messaging Application
   │
   ├── Presence Application
   │
   ├── Matching / Pairing Application
   │
   └── Call Application
   │
   ▼
Redis
   ├── Presence
   ├── Pub/Sub
   ├── Rate limits
   ├── Pairing queue
   └── Temporary call/signaling state
   │
   ▼
PostgreSQL
   ├── Messages
   ├── Call metadata/history
   ├── Friend/block relationships
   ├── Profile/matching data
   └── Reports/feedback
```

---

# 4. REST vs WebSocket vs WebRTC

Each technology has a different responsibility.

## REST

Use REST for:

- profile CRUD
- language configuration
- friend requests
- durable conversation retrieval
- message history retrieval
- call history
- feedback/reporting
- admin operations

## WebSocket

Use WebSocket for:

- presence
- message-send realtime events
- typing indicators
- read receipts
- incoming-call notification
- call state changes
- WebRTC signaling
- automatic pairing status

## WebRTC

Use WebRTC for:

- live voice media between users

The backend should not relay the normal voice media stream.

---

# 5. WebSocket Endpoint

Recommended:

```text
wss://api.talktribe/.../ws
```

Conceptual FastAPI route:

```text
/ws
```

Exact versioned path may be:

```text
/api/v1/ws
```

or:

```text
/ws/v1
```

Choose one convention and use it consistently.

The realtime protocol itself should also include a protocol/event version.

---

# 6. WebSocket Authentication

A WebSocket connection must be authenticated before becoming active.

Flow:

```text
Client
   ↓
Open WebSocket with auth credential
   ↓
Backend validates access token
   ↓
Validate:
- user exists
- account verified
- account active
   ↓
Bind socket to server-side user identity
   ↓
Register connection
```

Important:

Never trust a client event field such as:

```json
{
  "user_id": 123
}
```

as identity.

The sender identity comes from the authenticated connection.

---

# 7. Token Handling for WebSocket

Preferred options:

1. Secure cookie if frontend architecture supports it safely.
2. Short-lived connection token obtained through authenticated REST.
3. WebSocket subprotocol/auth mechanism supported by the client/server architecture.

Avoid long-lived JWTs in query-string URLs where they may leak into logs/history.

If query parameters are used temporarily during development, they must not become the production security design by accident.

---

# 8. Connection Manager

The WebSocket transport needs a connection manager.

Responsibilities:

- register connection
- unregister connection
- map user → active connection IDs
- send event to local connection
- support multiple devices/tabs
- heartbeat/liveness
- route events received from Redis Pub/Sub

Conceptually:

```text
ConnectionManager

user_id
  ├── connection_A
  ├── connection_B
  └── connection_C
```

Do not assume one WebSocket per user.

---

# 9. Connection Identity

Each socket should have a unique connection/session ID.

Example conceptual metadata:

```text
connection_id
user_id
connected_at
last_heartbeat_at
device/session metadata if required
```

Do not persist all connection state permanently in PostgreSQL.

Use memory + Redis as needed.

---

# 10. Presence Architecture

Presence means:

> The user is actively connected to TalkTribe.

Current product rules:

- online when the user enters/uses the application
- offline when they stop using the application
- exact last-seen display is not required in MVP
- realtime online/offline state is required

Presence should be derived from active connections.

---

# 11. Multi-Connection Presence

A user may have:

```text
browser tab 1
browser tab 2
mobile device
```

Therefore:

```text
user online
=
at least one active connection
```

User becomes offline only when the last active connection expires/disconnects.

---

# 12. Redis Presence Model

Conceptual keys:

```text
presence:user:{user_id}
connections:user:{user_id}
```

Possible representation:

```text
SET presence:user:123 online EX <ttl>
SET connections:user:123 <count/metadata>
```

Or Redis sets/hashes may be used.

Exact data structure should be selected during implementation.

Important requirements:

- use TTL
- heartbeat refreshes TTL
- stale connections disappear automatically
- Redis is transient
- PostgreSQL is not required for live presence

---

# 13. Heartbeat

WebSocket heartbeat prevents stale presence.

Flow:

```text
Client
   ↓ ping/heartbeat
Server
   ↓ update connection liveness
Redis
   ↓ refresh presence TTL
```

If heartbeats stop beyond the configured timeout:

```text
connection considered stale
   ↓
remove connection
   ↓
if no other connections
   ↓
user offline
```

Exact heartbeat interval is operational configuration.

---

# 14. Presence Events

Recommended events:

```text
presence.online
presence.offline
```

Potential later:

```text
presence.away
```

MVP only needs online/offline.

Do not broadcast global presence changes to every connected user.

Publish only to clients who need the information, such as:

- friends
- active conversation participants
- call target
- relevant UI context

---

# 15. Redis Pub/Sub

A single backend instance can send directly to its local connections.

Multiple backend instances require shared event distribution.

```text
Backend A
   ↓
Redis Pub/Sub
   ↓
Backend B
   ↓
User B socket
```

Redis Pub/Sub is intended for ephemeral realtime events.

It is not durable messaging storage.

---

# 16. Pub/Sub Event Envelope

Recommended internal event envelope:

```json
{
  "event_id": "uuid-or-generated-id",
  "type": "message.created",
  "version": 1,
  "timestamp": "UTC timestamp",
  "target_user_id": 456,
  "payload": {}
}
```

Internal Pub/Sub events and client-facing WebSocket events may use similar but separate schemas.

Do not expose internal-only metadata unnecessarily.

---

# 17. Client Event Envelope

Recommended client-facing structure:

```json
{
  "type": "message.send",
  "request_id": "client-generated-id",
  "payload": {}
}
```

Server response/event:

```json
{
  "type": "message.sent",
  "request_id": "same-client-id",
  "data": {},
  "error": null
}
```

The exact envelope should be finalized once and reused.

---

# 18. Event Versioning

Realtime event schemas change over time.

Recommended:

```text
event version = 1
```

Either include:

```json
"version": 1
```

or version the WebSocket protocol globally.

Do not silently change event payload shapes after frontend integration.

---

# 19. Event Authorization

Every event requires authorization.

Connection authentication only answers:

```text
Who is this?
```

Event authorization answers:

```text
Can this user perform this event?
```

Example:

```text
message.send
   ↓
Is sender allowed to interact with receiver?
   ↓
No block?
Messaging preference allows?
Conversation membership valid?
   ↓
Allowed / rejected
```

---

# 20. Messaging Realtime Flow

Recommended message-send flow:

```text
Client A
   ↓
message.send
   ↓
WebSocket Transport
   ↓
Messaging Application
   ↓
Validate:
- authenticated sender
- conversation access
- block state
- messaging permission
   ↓
Persist message in PostgreSQL
   ↓
Commit
   ↓
Publish message.created
   ↓
Redis Pub/Sub
   ↓
Backend holding Client B connection
   ↓
Client B
```

Durable persistence happens before successful realtime publication.

---

# 21. Message Acknowledgement

Client A should receive an acknowledgement.

Example:

```text
message.send
   ↓
database success
   ↓
message.sent
```

Payload can include:

```text
message_id
conversation_id
sent_at
```

This allows the frontend to reconcile temporary client messages with server-confirmed messages.

---

# 22. Message Delivery State

MVP requires delivery/read semantics.

Possible states:

```text
SENT
DELIVERED
READ
```

Recommended interpretation:

### SENT

Message is durably stored by the server.

### DELIVERED

Message event reached at least one active connection of the recipient.

### READ

Recipient explicitly opened/acknowledged the message/conversation.

Exact multi-device semantics need implementation-level definition.

---

# 23. Read Receipt Flow

```text
Client B opens/reads message
   ↓
message.read
   ↓
Messaging Application
   ↓
authorize participant
   ↓
persist read state
   ↓
publish message.read
   ↓
Client A
```

Read receipts are business state and should be persisted if the product expects them to survive reconnect.

---

# 24. Typing Indicator

Typing indicators are ephemeral.

Flow:

```text
Client A
   ↓
typing.start
   ↓
authorize conversation
   ↓
Redis / direct event
   ↓
Client B
```

Then:

```text
typing.stop
```

Typing state should not normally be persisted to PostgreSQL.

Use short TTLs to prevent stuck typing indicators.

---

# 25. Offline Messaging

If the recipient is offline:

```text
message persists in PostgreSQL
   ↓
no realtime delivery
   ↓
recipient reconnects later
   ↓
client retrieves unread/recent messages
```

Do not require Redis Pub/Sub to guarantee offline message delivery.

PostgreSQL is the source of truth.

---

# 26. Message Retention

Current requirement:

```text
message history retained for 1 week
```

A background cleanup process should remove expired messages.

Realtime transport must not assume messages older than retention are available.

---

# 27. Automatic Co-Learner Pairing

Automatic peer connection is a core TalkTribe experience.

Current product concept:

```text
User A wants to talk
User B wants to talk
        ↓
system automatically pairs them
```

Pairing should consider:

- active/available state
- no block relationship
- user eligibility
- English MVP
- compatible interests/hobbies/profession
- matching rules
- not already actively paired/in call
- other future constraints

---

# 28. Pairing vs Matching

These are related but different concepts.

## Matching

Answers:

> Which users are compatible?

Uses durable profile data and rule-based scoring.

## Pairing

Answers:

> Which currently waiting compatible user should I connect to now?

Uses:

```text
matching compatibility
+
current availability
+
waiting queue
```

Therefore:

```text
Matching Domain
       ↓ compatibility
Pairing / Call Application
       ↓ realtime availability
Redis Queue
```

---

# 29. Pairing Queue

Redis is suitable for the temporary waiting pool.

Conceptual:

```text
pairing:queue:english
```

A waiting user may have metadata:

```text
user_id
joined_at
interest/profile summary reference
matching bucket if used
```

Do not store full sensitive profiles in queue values unnecessarily.

---

# 30. Pairing Flow

```text
User A
   ↓
pairing.join
   ↓
Authenticate
   ↓
Check profile complete
   ↓
Check not blocked/suspended
   ↓
Check not already in call
   ↓
Mark available / add waiting
   ↓
Find compatible waiting candidate
   ↓
Matching rules
   ↓
Candidate User B
   ↓
Atomically reserve A + B
   ↓
Create call/pairing state
   ↓
pairing.matched → A
pairing.matched → B
   ↓
Voice-call signaling begins
```

---

# 31. Preventing Double Pairing

Race condition:

```text
A waits
B waits
C waits
```

Two backend workers must not pair B with both A and C.

Pair reservation must be atomic.

Possible Redis mechanisms:

- Lua script
- distributed lock used carefully
- atomic sorted-set/list/set operations
- transaction/watch pattern

Choose the simplest safe implementation.

At initial 50-user scale, correctness matters more than complex optimization.

---

# 32. Leaving Pairing Queue

Events:

```text
pairing.join
pairing.leave
pairing.waiting
pairing.matched
pairing.failed
```

A user should be removed from the waiting queue when:

- paired
- manually cancels
- WebSocket disconnects beyond grace period
- becomes unavailable
- account is suspended/blocked
- starts another call

Use TTL/cleanup to remove stale queue entries.

---

# 33. Pairing Timeout

Users should not wait indefinitely without UI state.

Architecture should support:

```text
waiting
still searching
cancel
no suitable partner found
```

Exact UX timeout is a product decision.

The backend should not fabricate a low-quality/blocked pairing just to satisfy a timeout.

---

# 34. Manual Friend Call

Manual call flow:

```text
User A opens friend
   ↓
Friend B is online
   ↓
User A selects Call
   ↓
call.start
   ↓
Backend checks:
- identity
- friend/contact permission if required
- block status
- B availability
- A not already in call
- B not already in call
   ↓
create RINGING call state
   ↓
call.incoming → B
```

B can:

```text
accept
reject
ignore → timeout/missed
```

---

# 35. Call State Machine

Recommended conceptual call states:

```text
CREATED
   ↓
RINGING
   ├── REJECTED
   ├── CANCELLED
   ├── MISSED
   └── ACCEPTED
          ↓
      CONNECTING
          ↓
        ACTIVE
          ↓
         ENDED
```

Failure path:

```text
CONNECTING
   ↓
FAILED
```

Exact persisted statuses can be simplified.

---

# 36. Durable vs Transient Call State

PostgreSQL:

- call ID
- participants
- high-level call status/history
- start/end timestamps
- duration
- outcome

Redis:

- ringing TTL
- active signaling session
- temporary offer/answer coordination if needed
- ICE signaling routing
- active-call lock/reservation

Frontend/WebRTC:

- media connection state
- local/remote tracks

---

# 37. WebRTC Signaling

WebRTC requires signaling but does not prescribe a signaling protocol.

TalkTribe uses WebSocket.

Typical sequence:

```text
User A
  ↓ call.start
Backend
  ↓ call.incoming
User B
  ↓ call.accept
Backend
  ↓ call.accepted
User A
  ↓ webrtc.offer
Backend
  ↓ relay
User B
  ↓ webrtc.answer
Backend
  ↓ relay
User A

Both sides:
ICE candidates
  ↕
Backend signaling relay
```

After negotiation:

```text
User A ⇄ WebRTC audio ⇄ User B
```

---

# 38. Signaling Event Types

Recommended conceptual events:

```text
call.start
call.incoming
call.accept
call.accepted
call.reject
call.rejected
call.cancel
call.cancelled
call.end
call.ended
call.missed

webrtc.offer
webrtc.answer
webrtc.ice-candidate
```

Server should validate that the sender belongs to the referenced call before relaying any signaling event.

---

# 39. STUN

STUN helps a WebRTC client discover its public-facing network address.

Development may use a public/free STUN service where appropriate.

Production should document the chosen provider.

STUN does not guarantee connectivity across all NAT/firewall environments.

---

# 40. TURN

TURN relays media when direct peer-to-peer connection cannot be established.

For a real voice-call product, TURN should be considered necessary for reliable connectivity.

Architecture:

```text
Try direct WebRTC
      ↓
STUN-assisted P2P
      ↓ if unavailable
TURN relay
```

TURN provider/hosting is an infrastructure decision.

Potential approaches:

- self-hosted coturn
- managed TURN provider

Initial cost and operational complexity should be evaluated later.

---

# 41. TURN Credentials

Do not expose permanent TURN admin credentials in frontend code.

Prefer short-lived TURN credentials when the selected TURN architecture supports them.

Backend may issue temporary connection credentials to authenticated call participants.

Exact implementation belongs in deployment/infrastructure planning.

---

# 42. Call Authorization During Signaling

For every signaling event:

```text
authenticated socket user
      ↓
load/verify active call state
      ↓
is sender caller/callee?
      ↓
is call currently in a valid state?
      ↓
relay only to the other participant
```

Never allow arbitrary:

```text
send offer to user_id X
```

without active-call authorization.

---

# 43. Call Concurrency

MVP rule should normally be:

```text
one active/ringing voice call per user
```

This simplifies:

- availability
- pairing
- signaling
- UI
- presence

Redis can maintain:

```text
call_active:user:{user_id}
```

with safe TTL/cleanup.

Exact policy should be confirmed in workflow design.

---

# 44. Call Disconnect

Possible cases:

- user presses end
- WebSocket disconnect
- WebRTC media disconnect
- network changes
- browser closes
- TURN fails

Do not immediately mark every short WebSocket interruption as a finished call.

Provide a small reconnection/grace strategy.

---

# 45. Reconnection

WebSocket reconnect flow:

```text
connection lost
   ↓
frontend retries with backoff
   ↓
authenticate new connection
   ↓
restore server-visible session state
```

For messaging:

```text
retrieve missed messages/read state
```

For active call:

```text
if call still valid within grace period
   ↓
restore signaling state or renegotiate
```

Exact call reconnection behavior can be simplified for MVP if necessary.

---

# 46. Reconnection Backoff

Frontend should not reconnect in a tight loop.

Use exponential backoff with jitter.

Conceptually:

```text
1s
2s
4s
8s
...
```

with a reasonable cap.

Exact values are client implementation details.

---

# 47. Multiple Backend Instances

Initial MVP may run one FastAPI instance.

Architecture should still avoid assumptions that make a second instance impossible.

Single instance:

```text
Client A → Backend A ← Client B
```

Multiple instances:

```text
Client A → Backend A
               │
             Redis
               │
Client B → Backend B
```

Redis Pub/Sub/coordination bridges instances.

---

# 48. Pub/Sub Channel Design

Avoid one Redis channel per user if it creates unnecessary operational complexity.

Possible design:

```text
talktribe:events
```

with target IDs in event payloads, or partitioned channels.

Another option:

```text
user:{user_id}:events
```

At MVP scale either can work.

Choose based on implementation simplicity and Redis client behavior.

Do not prematurely optimize.

---

# 49. Realtime Error Envelope

Example:

```json
{
  "type": "error",
  "request_id": "abc123",
  "error": {
    "code": "CALL_NOT_ALLOWED",
    "message": "The call cannot be started."
  }
}
```

Stable error codes should be shared with REST error conventions where applicable.

Do not expose internal stack traces.

---

# 50. Event Idempotency

Clients may retry after network failure.

Commands such as:

```text
call.end
call.cancel
message.read
pairing.leave
```

should be tolerant of repeated delivery where possible.

Use:

```text
request_id
event_id
```

where helpful.

For message creation, duplicate-send prevention may use a client-generated message ID/idempotency key if retries become an observed problem.

---

# 51. Ordering

WebSocket preserves message ordering on one connection, but distributed Pub/Sub/reconnect can complicate global ordering.

For durable messages use server timestamps and database IDs/order.

Client should order conversation history based on server-authoritative fields.

Do not treat client timestamps as authoritative.

---

# 52. Presence Privacy

Presence is not necessarily globally public.

Only expose presence when product rules permit.

Likely MVP:

- friends can see online status
- matching/pairing internally uses availability
- profile display may show online status according to product decision

Do not expose a global list of every online user.

---

# 53. Pairing Privacy

The pairing queue is internal infrastructure.

Clients should not receive:

- raw queue contents
- other waiting user IDs before match
- internal compatibility candidate lists

They should receive only their own state:

```text
waiting
matched
cancelled
failed
```

---

# 54. Realtime Rate Limiting

Rate-limit event types that can be abused:

```text
message.send
typing.start
pairing.join
call.start
webrtc signaling spam
reports
```

Typing events especially should be throttled/debounced client-side and protected server-side.

---

# 55. Realtime Logging

Log useful metadata:

```text
connection_id
user_id
event type
call_id
conversation_id
request_id
result
duration
```

Do not log:

- message content by default
- SDP offer/answer unless debugging in a safe environment
- ICE credentials
- tokens
- private chat payloads unnecessarily

---

# 56. Metrics

Useful future metrics:

```text
active WebSocket connections
online users
pairing queue length
average pairing wait time
pairing success rate
messages sent
message delivery latency
active calls
call connection success rate
call failures
average call duration
TURN relay usage
```

Start simple; add observability as deployment matures.

---

# 57. Background Cleanup

Realtime-related cleanup jobs:

- stale pairing queue entries
- expired call state
- expired presence keys handled via TTL
- one-week message retention
- old call-signaling temporary state
- expired rate-limit keys handled by TTL

Do not create background jobs for state Redis can safely expire with TTL.

---

# 58. Failure Handling

## Redis unavailable

Effects may include:

- presence unavailable
- Pub/Sub unavailable
- pairing unavailable
- realtime cross-instance routing unavailable

Durable PostgreSQL data remains safe.

The app should fail gracefully rather than silently claiming realtime success.

## PostgreSQL unavailable

Do not acknowledge durable message/call operations as successful.

## WebSocket unavailable

Frontend may still use REST features, but realtime chat/calling becomes unavailable.

## TURN unavailable

Direct P2P calls may still work for some users, but reliability decreases.

---

# 59. Realtime Health

Readiness checks may include Redis connectivity if realtime capability is considered mandatory for accepting traffic.

Possible health separation:

```text
/health/live
/health/ready
```

Readiness may report degraded realtime infrastructure according to deployment policy.

---

# 60. Testing Strategy

## WebSocket connection tests

- authenticated connection succeeds
- invalid token rejected
- suspended user rejected
- disconnect cleans state
- multiple connections maintain presence correctly

## Presence tests

- first connection → online
- additional connection → still online
- one of multiple disconnects → still online
- final disconnect/TTL → offline

## Messaging tests

- authorized send
- blocked send denied
- message persisted
- receiver gets event
- offline message persisted
- read receipt
- typing event not persisted

## Pairing tests

- join queue
- leave queue
- compatible users paired
- blocked users never paired
- user cannot be double-paired
- disconnected waiting user removed
- active-call user cannot join

## Call tests

- manual call eligible friend
- blocked call denied
- unavailable target handled
- accept/reject/cancel/end
- unauthorized offer rejected
- ICE relay only between participants
- one active call per user
- timeout → missed call

## Multi-instance tests later

- A connected to backend 1
- B connected to backend 2
- Redis Pub/Sub delivers event correctly

---

# 61. Initial Scale

Planning assumption:

```text
~50 initial users
```

Therefore MVP does not need:

- Kafka
- dedicated realtime microservice
- complex distributed scheduler
- service mesh
- multi-region realtime routing

One FastAPI deployment + Redis is sufficient initially.

The Redis-backed design preserves a path to multiple backend instances later.

---

# 62. Suggested Realtime Package Structure

Possible target:

```text
app/
├── realtime/
│   ├── websocket/
│   │   ├── router.py
│   │   ├── connection_manager.py
│   │   ├── events.py
│   │   └── dispatcher.py
│   │
│   └── signaling/
│       └── schemas.py
│
├── domains/
│   ├── messaging/
│   ├── presence/
│   ├── matching/
│   └── calls/
│
└── infrastructure/
    └── redis/
        ├── client.py
        ├── pubsub.py
        └── repositories.py
```

Business event handling should delegate to domain/application services.

---

# 63. Implementation Sequence

Realtime should be built incrementally.

```text
1. Redis async client
2. Authenticated WebSocket endpoint
3. ConnectionManager
4. Presence
5. Pub/Sub abstraction
6. Basic event envelope/dispatcher
7. Pairing queue
8. Automatic co-learner pairing
9. Voice call state
10. WebRTC signaling
11. STUN/TURN integration
12. Messaging realtime events
13. Read receipts
14. Typing indicators
15. Reconnection hardening
16. Multi-instance validation
```

The exact order of Messaging vs Calls may be adjusted based on feature roadmap, but voice connection is the core MVP requirement.

---

# 64. Decisions to Record as ADRs

Likely ADRs from this architecture:

```text
Use WebSocket for realtime transport
Use Redis for presence/PubSub/pairing
Use WebRTC for voice media
Backend handles signaling, not media relay
Use TURN fallback for production reliability
Keep realtime inside modular monolith initially
Persist messages/call metadata in PostgreSQL
```

These should later become individual ADR files.

---

# 65. Open Realtime Decisions

Still to finalize:

1. Exact WebSocket URL/versioning.
2. Authentication mechanism used during WebSocket handshake.
3. Heartbeat interval and presence TTL.
4. Presence visibility rules.
5. Exact event envelope.
6. Redis Pub/Sub channel strategy.
7. Pairing wait timeout.
8. Exact automatic-pairing ranking logic when multiple users are waiting.
9. Whether recently paired users should be temporarily excluded from rematching.
10. One active call per user confirmation.
11. Ringing timeout.
12. Call reconnection grace period.
13. STUN/TURN provider.
14. TURN credential approach.
15. Whether call history stores unsuccessful call attempts.
16. Detailed message delivery/read semantics for multiple devices.
17. Whether realtime message sending also needs REST fallback.
18. Exact order in which chat vs voice-call feature implementation occurs.

---

# 66. Realtime Architecture Summary

```text
                         React Client
                 ┌──────────┼───────────┐
                 │          │           │
                REST    WebSocket     WebRTC
                 │          │           │
                 ▼          ▼           │
              FastAPI  Realtime Layer   │
                 │          │           │
                 │    ┌─────┼─────┐     │
                 │    ▼     ▼     ▼     │
                 │ Presence Chat  Calls │
                 │    │     │     │     │
                 │    └─────┼─────┘     │
                 │          │           │
                 ▼          ▼           │
            PostgreSQL    Redis         │
                 ▲          │           │
                 │          │           │
                 │       signaling      │
                 │          │           │
                 └──────────┴───────────┘

Voice media:
User A  ⇄  WebRTC/STUN/TURN  ⇄  User B
```

---

# 67. Next Architecture Artifact

```text
REQUIREMENTS_BASELINE.md       ✅
DOMAIN_BOUNDARIES.md           ✅
COMPONENT_ARCHITECTURE.md      ✅
DATABASE_ARCHITECTURE.md       ✅
API_ARCHITECTURE.md            ✅
SECURITY_ARCHITECTURE.md       ✅
REALTIME_ARCHITECTURE.md       ✅
        ↓
TARGET_ARCHITECTURE.md         ← NEXT
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
