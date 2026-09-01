# TalkTribe Voice Call Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** Calls / Peer Connection  
**Depends on:** `PAIRING_WORKFLOW.md`, `PRESENCE_WORKFLOW.md`, `FRIENDSHIP_WORKFLOW.md`, `REALTIME_ARCHITECTURE.md`, `SECURITY_ARCHITECTURE.md`

---

# 1. Purpose

This document defines the end-to-end MVP voice-call workflow.

It covers:

- automatic-pairing calls
- manual friend calls
- call eligibility
- call states
- WebSocket signaling
- WebRTC offer/answer/ICE
- STUN/TURN
- call accept/reject/cancel/end
- disconnection and reconnection
- call history
- post-call handoff to feedback/reporting
- testing
- Definition of Done

Voice is part of MVP.

Video is future scope.

---

# 2. Voice Call Goals

TalkTribe must support:

```text
Automatic paired learner call
Manual online-friend call
```

The backend controls:

```text
authentication
authorization
call lifecycle
signaling
availability
call metadata
```

The browser handles:

```text
microphone
WebRTC media
audio tracks
peer connection
```

---

# 3. Call Modes

Recommended conceptual call source:

```text
PAIRING
FRIEND_MANUAL
```

This can be stored as call metadata if useful.

---

# 4. Manual Friend Call Preconditions

Caller must:

```text
be authenticated
be ACTIVE
be online
not already in call
```

Target must:

```text
exist
be ACTIVE
be online
be a friend
not be blocked in either direction
not already in call
be available
```

---

# 5. Automatic Pairing Call Preconditions

For automatically paired users:

```text
pairing has already validated compatibility
both reserved
both online
block rules satisfied
```

Call service still validates current state before signaling.

---

# 6. Call State Machine

Recommended:

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

Failure:

```text
CONNECTING → FAILED
```

Automatic pairing may simplify or shorten the RINGING step depending on UX.

---

# 7. Manual Call Start

```text
User A selects Call on Friend B
        ↓
call.start
        ↓
Authenticate A
        ↓
Validate friendship/block state
        ↓
Validate B online/available
        ↓
Atomically reserve call availability for A+B
        ↓
Create call record/state
        ↓
call.incoming → B
        ↓
call.ringing → A
```

---

# 8. Incoming Call

Target receives:

```text
caller safe profile summary
call_id
call type
```

Possible actions:

```text
accept
reject
ignore
```

---

# 9. Accept Call

```text
B → call.accept
        ↓
authenticate B
        ↓
verify B is callee/participant
        ↓
verify state RINGING
        ↓
state → ACCEPTED / CONNECTING
        ↓
notify A
        ↓
start WebRTC negotiation
```

---

# 10. Reject Call

```text
B → call.reject
        ↓
verify participant/state
        ↓
state → REJECTED
        ↓
release availability locks
        ↓
notify A
```

---

# 11. Caller Cancel

Before acceptance:

```text
A → call.cancel
        ↓
verify caller/state
        ↓
state → CANCELLED
        ↓
release reservations
        ↓
notify B
```

---

# 12. Missed Call

If B does not respond within ringing timeout:

```text
RINGING
   ↓ timeout
MISSED
```

Release both users from temporary call reservation.

Exact timeout remains configurable.

---

# 13. WebRTC Signaling

After acceptance:

```text
A creates WebRTC offer
        ↓
webrtc.offer
        ↓
Backend validates A belongs to call
        ↓
relay to B
        ↓
B sets remote description
        ↓
B creates answer
        ↓
webrtc.answer
        ↓
Backend validates B belongs to call
        ↓
relay to A
```

ICE candidates are exchanged similarly.

---

# 14. ICE Candidate Flow

```text
peer gathers candidate
        ↓
webrtc.ice-candidate
        ↓
backend verifies call participation
        ↓
relay only to other participant
```

Clients must not choose arbitrary target user IDs for signaling.

---

# 15. STUN / TURN

Connection attempt:

```text
direct WebRTC
   ↓
STUN-assisted NAT discovery
   ↓
TURN relay fallback
```

TURN is needed for production reliability when direct connectivity fails.

---

# 16. Media Security Boundary

FastAPI should not carry normal audio media.

Media path:

```text
User A ⇄ WebRTC ⇄ User B
```

or:

```text
User A ⇄ TURN ⇄ User B
```

Backend signaling path is separate.

---

# 17. Microphone Permission

Frontend must request microphone permission.

If denied:

```text
call cannot become ACTIVE
```

Client should report a usable error.

Backend may transition call to:

```text
FAILED
```

if setup cannot complete.

---

# 18. Active Call

Once WebRTC connection succeeds:

```text
state → ACTIVE
answered_at/start time recorded
```

During active call:

```text
both users unavailable for new calls
both users unavailable for pairing
```

---

# 19. One Active Call Rule

Recommended MVP:

```text
one active/ringing call per user
```

This should be enforced with atomic transient state in Redis plus durable call state where needed.

---

# 20. End Call

Either participant may:

```text
call.end
```

Flow:

```text
validate participant
   ↓
state ACTIVE?
   ↓
state → ENDED
   ↓
ended_at
   ↓
duration calculated
   ↓
release call locks
   ↓
notify both
   ↓
feedback/reporting flow available
```

---

# 21. Duplicate End

`call.end` should be idempotent where possible.

Repeated end requests must not create inconsistent durations or states.

---

# 22. WebSocket Disconnect During Call

A short signaling socket loss should not necessarily immediately destroy an otherwise active WebRTC media connection.

Possible MVP behavior:

```text
disconnect
   ↓
short grace
   ↓
reconnect?
  ├── yes → restore signaling context
  └── no  → end/fail call according to policy
```

Exact grace remains open.

---

# 23. WebRTC Disconnect

If peer connection fails:

```text
attempt ICE restart/reconnect if simple
```

If recovery fails:

```text
state → FAILED or ENDED
release availability
```

MVP should prefer simple predictable recovery over highly complex call recovery logic.

---

# 24. Call History

PostgreSQL may store:

```text
call_id
caller
callee
source/type
status
created_at
answered_at
ended_at
duration
```

Do not store voice media.

---

# 25. Call History API

Possible:

```text
GET /api/v1/calls
GET /api/v1/calls/{call_id}
```

Only call participants and authorized admins may access appropriate call metadata.

---

# 26. Post-Call Flow

After completed call:

```text
call.ended
   ↓
frontend shows:
Rate learner
Report learner
Find another learner
```

Feedback/reporting is a separate workflow.

---

# 27. Blocking After Call

If user blocks their partner after the call:

```text
future matching denied
future messaging denied
future calls denied
friend requests denied
```

Current call history/feedback remains according to data-retention rules.

---

# 28. Call Events

Recommended:

```text
call.start
call.incoming
call.ringing
call.accept
call.accepted
call.reject
call.rejected
call.cancel
call.cancelled
call.missed
call.connected
call.end
call.ended
call.failed

webrtc.offer
webrtc.answer
webrtc.ice-candidate
```

---

# 29. Error Codes

```text
CALL_NOT_ALLOWED
CALL_TARGET_OFFLINE
CALL_TARGET_BUSY
CALLER_BUSY
CALL_NOT_FOUND
CALL_STATE_INVALID
CALL_PARTICIPANT_REQUIRED
CALL_ALREADY_ENDED
CALL_SIGNALING_NOT_ALLOWED
MICROPHONE_REQUIRED
CALL_CONNECTION_FAILED
```

---

# 30. Security

For every call/signaling event:

```text
authenticated socket user
   ↓
participant?
   ↓
valid call state?
   ↓
interaction still allowed?
```

Do not trust frontend route state or supplied sender ID.

---

# 31. Rate Limiting

Protect:

```text
call.start
```

from spam.

Potential limits:

```text
per caller
per target
per time window
```

Exact values belong in configuration.

---

# 32. Failure Handling

## Redis unavailable

Cannot safely manage availability/signaling coordination.

```text
calls degraded/unavailable
```

## PostgreSQL unavailable

If durable call creation is mandatory:

```text
do not acknowledge call creation
```

## TURN unavailable

Some direct calls may work, but reliability falls.

## WebSocket unavailable

Call setup/signaling unavailable.

---

# 33. Testing

- eligible manual friend call
- non-friend manual call denied
- blocked call denied
- offline target denied
- busy target denied
- caller already in call denied
- accept works
- reject works
- cancel works
- missed timeout works
- offer only from participant
- answer only from participant
- ICE relay only within active call
- one active call per user
- call end releases state
- duplicate end safe
- call duration recorded
- disconnect cleanup
- paired call handoff works
- feedback enabled only after appropriate call state

---

# 34. Definition of Done — Voice Calls

- [ ] Manual online-friend call works.
- [ ] Automatic paired-call flow works.
- [ ] Call eligibility is enforced.
- [ ] One active/ringing call per user is enforced.
- [ ] Call state machine is consistent.
- [ ] WebSocket signaling works.
- [ ] Offer/answer/ICE are authorized.
- [ ] WebRTC audio connects.
- [ ] STUN configured.
- [ ] TURN fallback strategy exists for production.
- [ ] Reject/cancel/missed/end work.
- [ ] Call metadata is persisted as required.
- [ ] Availability is released reliably.
- [ ] Blocked users cannot call.
- [ ] Post-call flow reaches Feedback/Reporting.
- [ ] Automated call/signaling tests pass.

---

# 35. Open Decisions

1. Ring timeout.
2. Call reconnect grace.
3. Exact TURN provider.
4. TURN credential generation.
5. Whether paired calls require explicit accept from both users.
6. Whether all failed attempts are persisted.
7. Call history retention.
8. Exact client ICE restart behavior.
9. Whether calls can be muted/held in MVP.
10. Exact rating prompt timing.

---

# 36. Workflow Diagram

```text
CALL REQUEST / PAIRED USERS
          ↓
VALIDATE ELIGIBILITY
          ↓
RESERVE BOTH USERS
          ↓
RINGING / ACCEPT
          ↓
WEBRTC OFFER
          ↓
WEBRTC ANSWER
          ↓
ICE CANDIDATES
          ↓
STUN / TURN
          ↓
VOICE CONNECTED
          ↓
ACTIVE CALL
          ↓
END / FAILURE
          ↓
RELEASE AVAILABILITY
          ↓
FEEDBACK / REPORT
```
