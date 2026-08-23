# TalkTribe Messaging Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** Messaging  
**Depends on:** `FRIENDSHIP_WORKFLOW.md`, `PRESENCE_WORKFLOW.md`, `REALTIME_ARCHITECTURE.md`, `DATABASE_ARCHITECTURE.md`, `SECURITY_ARCHITECTURE.md`

---

# 1. Purpose

This document defines TalkTribe MVP one-to-one messaging.

It covers:

- conversation creation/access
- messaging eligibility
- WebSocket sending
- PostgreSQL persistence
- online/offline delivery
- delivery/read state
- typing indicators
- blocking
- one-week retention
- authorization
- failure handling
- testing
- Definition of Done

---

# 2. MVP Messaging Decision

MVP supports:

```text
1:1 messaging
message persistence
online/offline delivery behavior
typing indicators
delivery/read receipts
```

Current retention decision:

```text
message history = 1 week
```

---

# 3. Friendship Is Not Always Required

Current product rule:

```text
users may message without friendship if recipient/user messaging permission allows it
```

At minimum:

```text
no block
active accounts
messaging eligibility
```

Exact privacy-preference options remain open.

---

# 4. Conversation Model

MVP conversation type:

```text
DIRECT
```

Each direct conversation has exactly two active participants.

Durable tables:

```text
conversations
conversation_participants
messages
```

---

# 5. Conversation Creation

Possible workflow:

```text
User A chooses Message User B
        ↓
validate interaction eligibility
        ↓
existing direct conversation?
   ├── yes → return it
   └── no  → create conversation
```

This avoids duplicate direct conversations for the same pair.

---

# 6. Conversation Access

Only a conversation participant may:

```text
view conversation
retrieve messages
send message
mark messages read
```

Non-participant:

```text
403 / CONVERSATION_ACCESS_DENIED
```

---

# 7. Send Message Flow

```text
Client A
   ↓
message.send
   ↓
authenticated WebSocket
   ↓
Messaging Application
   ↓
validate:
- sender participant
- recipient valid
- no block
- messaging preference allows
   ↓
BEGIN
   insert message
COMMIT
   ↓
message.sent → A
   ↓
recipient online?
  ├── yes → publish realtime event
  └── no  → remain stored for later
```

Persistence occurs before success acknowledgement.

---

# 8. Message Event

Example:

```json
{
  "type": "message.send",
  "request_id": "abc123",
  "payload": {
    "conversation_id": 88,
    "content": "Hello!"
  }
}
```

Server derives sender identity from the socket.

---

# 9. Message Acknowledgement

After persistence:

```text
message.sent
```

May include:

```text
message_id
conversation_id
sent_at
```

Frontend reconciles temporary/local message state.

---

# 10. Recipient Delivery

If recipient is online:

```text
message.created
```

is delivered to one or more active recipient connections.

If multiple devices are connected, delivery semantics should be defined consistently.

---

# 11. SENT / DELIVERED / READ

Recommended semantics:

## SENT

```text
server persisted message
```

## DELIVERED

```text
message reached at least one active recipient connection
```

## READ

```text
recipient explicitly acknowledged/opened message
```

Exact multi-device aggregation remains an implementation detail.

---

# 12. Offline Recipient

```text
message stored
recipient offline
```

No data is lost.

On reconnect:

```text
client loads conversation/recent unread messages
```

Redis Pub/Sub is not relied upon for offline delivery.

---

# 13. Retrieve Messages

Recommended:

```text
GET /api/v1/conversations/{id}/messages
```

Must be paginated.

Cursor pagination is preferred for ordered message history.

---

# 14. Read Receipt Flow

```text
Recipient views messages
        ↓
message.read
        ↓
verify conversation participant
        ↓
persist read state
        ↓
publish message.read to sender
```

---

# 15. Typing Indicator

Typing is ephemeral.

```text
typing.start
typing.stop
```

Flow:

```text
validate conversation membership
   ↓
relay to other participant
```

Do not persist typing state in PostgreSQL.

Use debounce/throttle and TTL.

---

# 16. Blocking

Current decision:

```text
existing conversation remains
new message exchange stops
```

If A blocks B:

```text
message.send between A/B → denied
```

Conversation history remains until retention cleanup.

---

# 17. Message Retention

Current business rule:

```text
7 days
```

A background cleanup process deletes expired messages.

Conceptual:

```text
sent_at < now - 7 days
```

Exact deletion batching/soft-delete choice remains open.

---

# 18. Message Content

MVP supports text messaging.

Possible validation:

```text
non-empty
max length
safe text encoding
```

Do not render untrusted text as raw HTML on frontend.

---

# 19. Abuse

Product rules disallow abusive/unethical language.

MVP architecture should support:

```text
user reporting
block
admin moderation
```

Automated content moderation is not yet a defined requirement.

---

# 20. Messaging Preference

Exact model remains open.

Possible future values:

```text
ANY_ELIGIBLE_USER
FRIENDS_ONLY
```

Messaging service should consume a permission contract rather than hardcode friendship everywhere.

---

# 21. Presence Integration

Presence answers:

```text
is recipient online?
```

Messaging decides:

```text
can sender send?
persist message?
```

Presence is delivery optimization/state, not durable permission.

---

# 22. Redis Integration

Redis may carry:

```text
message realtime event
typing event
read/delivery notification
```

PostgreSQL stores durable message truth.

---

# 23. Multiple Backend Instances

```text
A → Backend 1
B → Backend 2
```

Flow:

```text
Backend 1 persists message
   ↓
Redis Pub/Sub
   ↓
Backend 2
   ↓
B socket
```

---

# 24. REST API

Recommended:

```text
GET  /api/v1/conversations
POST /api/v1/conversations
GET  /api/v1/conversations/{id}
GET  /api/v1/conversations/{id}/messages
```

Sending should primarily use WebSocket.

REST send fallback is optional and currently open.

---

# 25. Error Codes

```text
CONVERSATION_NOT_FOUND
CONVERSATION_ACCESS_DENIED
MESSAGE_NOT_ALLOWED
USER_BLOCKED
MESSAGE_EMPTY
MESSAGE_TOO_LONG
MESSAGING_PERMISSION_DENIED
REALTIME_CONNECTION_REQUIRED
```

---

# 26. Idempotency

Network retry can duplicate sends.

Potential solution:

```text
client_message_id
```

stored/checked per sender/conversation if duplicate sends become a practical problem.

This can be added during implementation if needed.

Read receipt and typing events should naturally tolerate retries.

---

# 27. Authorization

For every message action:

```text
authenticated sender
conversation participant
active account
block state valid
messaging preference valid
```

Never trust supplied sender user ID.

---

# 28. Privacy

Do not expose:

```text
other conversations
private auth data
message content to non-participants
```

Admin access to message content is not automatically allowed and remains a moderation-policy decision.

---

# 29. Failure Handling

## PostgreSQL failure

```text
do not acknowledge message as sent
```

## Redis failure after DB commit

Message remains durable.

Sender can receive sent acknowledgement but realtime delivery may be delayed/unavailable depending implementation.

## Recipient disconnect

Message remains in PostgreSQL.

---

# 30. Frontend Flow

```text
Open conversation
   ↓
load recent messages
   ↓
WebSocket active
   ↓
send message
   ↓
temporary local state
   ↓
message.sent
   ↓
server-confirmed state
```

Incoming message updates UI immediately.

---

# 31. Testing

- participant can create/access direct conversation
- duplicate direct conversation avoided
- non-participant denied
- message persists before ack
- blocked user denied
- messaging permission enforced
- offline recipient message remains
- online recipient receives event
- delivered state works
- read state works
- typing not persisted
- message retention works
- private conversation not exposed
- multi-instance Pub/Sub later validated

---

# 32. Definition of Done — Messaging

- [ ] Direct conversations work.
- [ ] Only participants can access conversations.
- [ ] Message sending is realtime.
- [ ] Message is persisted before success acknowledgement.
- [ ] Offline recipients do not lose messages.
- [ ] Online recipients receive events.
- [ ] Blocking prevents new messages.
- [ ] Messaging permission model is enforced.
- [ ] Typing indicators work.
- [ ] Delivery/read state works.
- [ ] Message history is paginated.
- [ ] One-week retention is enforced.
- [ ] Redis is not durable message storage.
- [ ] Sensitive data is not exposed.
- [ ] Automated tests pass.

---

# 33. Open Decisions

1. Exact messaging preference model.
2. REST send fallback.
3. Maximum message length.
4. Hard-delete vs tombstone after 7 days.
5. Multi-device delivery/read semantics.
6. Client message id/idempotency.
7. Whether users can delete individual messages.
8. Whether admins can inspect content during moderation.
9. Conversation retention after all messages expire.

---

# 34. Workflow Diagram

```text
USER A SENDS MESSAGE
        ↓
WEBSOCKET
        ↓
AUTH + CONVERSATION CHECK
        ↓
BLOCK / PERMISSION CHECK
        ↓
PERSIST POSTGRESQL
        ↓
ACK USER A
        ↓
RECIPIENT ONLINE?
   ┌────┴────┐
   │         │
  YES       NO
   │         │
   ▼         ▼
REDIS/WS   STORED
   │         │
   ▼         ▼
USER B   LOAD LATER
   │
   ▼
READ RECEIPT
```
