# ADR-013: Retain Message History for One Week

**Status:** Accepted

## Context

The current product decision states that chat message history should remain available for one week.

## Decision

Persist messages in PostgreSQL and retain them for approximately **7 days**.

A cleanup/background process will remove expired messages.

## Alternatives Considered

### Permanent message history
Rejected because it conflicts with the current product decision and increases storage/privacy burden.

### Redis-only messages
Rejected because Redis is not the durable system of record.

### No persistence
Rejected because offline delivery and conversation continuity require durable messages.

## Consequences

### Positive
- Supports offline/recent message access
- Limits long-term data storage
- Clear retention policy

### Negative
- Requires cleanup job
- Users cannot retrieve older conversations after retention expiry

## Open Detail

Hard deletion vs tombstone behavior should be finalized during implementation.
