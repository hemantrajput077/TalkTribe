# ADR-014: Defer Notifications Until After Peer-to-Peer Connection

**Status:** Accepted

## Context

Notifications were initially discussed alongside MVP communication features, but the product decision is to prioritize the peer-to-peer connection experience first.

## Decision

Notifications are **post-core-P2P work**.

TalkTribe will first establish:

- authentication
- profile
- matching
- friendship/blocking
- realtime foundation
- automatic pairing
- voice connection
- messaging

Then notification functionality may be introduced.

## Alternatives Considered

### Build notification infrastructure early
Rejected because it increases MVP scope before the core communication experience exists.

### Remove notifications permanently
Rejected because notifications remain useful future functionality.

## Consequences

### Positive
- Keeps MVP architecture focused
- Reduces premature infrastructure
- Allows notification design to use real events from completed domains

### Negative
- Some user reminders/alerts will not exist initially

## Future Direction

Notifications should consume explicit application/domain events rather than forcing Friendship, Messaging, or Calls to own delivery infrastructure.
