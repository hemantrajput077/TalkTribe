# ADR-004: Use Redis for Realtime Coordination

**Status:** Accepted

## Context

TalkTribe needs transient and distributed state for presence, WebSocket Pub/Sub, pairing, call signaling coordination, rate limiting, and caching.

## Decision

Use **Redis** for:

- online/offline presence
- WebSocket Pub/Sub
- pairing queues
- temporary call state
- rate limiting
- short-lived caching
- coordination between backend instances

## Alternatives Considered

### PostgreSQL for presence and transient state
Rejected because frequent ephemeral updates would create unnecessary durable database load.

### In-memory process state only
Rejected as the target design because it fails when multiple backend instances are introduced.

### Kafka
Rejected for MVP as excessive for current scale and requirements.

## Consequences

### Positive
- Fast transient state
- TTL support
- Pub/Sub
- Supports future horizontal scaling

### Negative
- Redis availability affects realtime features
- Pub/Sub is not durable
- Requires clear separation from PostgreSQL responsibilities

## Rule

Redis outage may degrade realtime functionality, but must not cause loss of durable business history.
