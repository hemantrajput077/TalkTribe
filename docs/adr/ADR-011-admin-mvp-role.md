# ADR-011: Include Admin as an MVP Role

**Status:** Accepted

## Context

Earlier planning treated Admin as future work, but the product decision was changed: TalkTribe requires an admin role in MVP for moderation and user management.

## Decision

Include:

```text
USER
ADMIN
```

as MVP roles.

Admin operations will live behind explicit authorization and should be audited when sensitive.

## Alternatives Considered

### No Admin in MVP
Rejected because moderation and privileged user management are now explicit MVP requirements.

### Separate Admin microservice
Rejected as unnecessary.

## Consequences

### Positive
- Moderation foundation exists from MVP
- Security model accounts for privileged operations early

### Negative
- Authorization design must be completed earlier
- Admin functionality increases MVP scope

## Rule

Admin is not a bypass around domain boundaries. Admin actions should use approved application/domain contracts.
