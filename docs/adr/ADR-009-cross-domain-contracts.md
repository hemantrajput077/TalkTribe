# ADR-009: Cross-Domain Communication Through Contracts

**Status:** Accepted

## Context

A modular monolith shares one process and database, making it easy for one module to import and mutate another module's repository. That would destroy domain boundaries over time.

## Decision

Cross-domain interactions must go through explicit application contracts, interfaces, facades, or query services.

Example:

```text
Messaging → FriendshipEligibility
```

not:

```text
Messaging → FriendshipRepository
```

## Alternatives Considered

### Direct repository imports
Rejected because they create strong coupling and leak data ownership.

### Event-only communication
Rejected as the universal approach because many MVP interactions are synchronous and simpler as direct application contracts.

## Consequences

### Positive
- Clear ownership
- Easier testing
- Easier later extraction of domains
- Limits coupling

### Negative
- Requires small interface/facade design
- Can feel more verbose than direct imports

## Rule

A domain may not directly modify another domain's persistence.
