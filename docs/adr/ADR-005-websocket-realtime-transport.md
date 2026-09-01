# ADR-005: Use WebSocket for Realtime Transport

**Status:** Accepted

## Context

TalkTribe requires realtime messaging, presence, pairing status, incoming-call events, read receipts, typing indicators, and WebRTC signaling.

## Decision

Use **WebSocket** as the primary bidirectional realtime transport.

REST remains responsible for normal durable request/response operations.

## Alternatives Considered

### HTTP polling
Rejected because it produces unnecessary latency and request volume for realtime features.

### Server-Sent Events
Rejected because TalkTribe needs bidirectional client/server communication.

### Separate realtime service
Deferred because the modular monolith is sufficient initially.

## Consequences

### Positive
- Low-latency bidirectional communication
- One transport for chat, presence, pairing, and signaling
- Integrates with Redis Pub/Sub for multi-instance routing

### Negative
- Requires connection lifecycle management
- Requires reconnect handling
- Requires event-level authorization

## Rule

WebSocket handlers are transport adapters and must delegate business rules to application/domain services.
