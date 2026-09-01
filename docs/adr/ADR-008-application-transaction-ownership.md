# ADR-008: Application Layer Owns Transactions

**Status:** Accepted

## Context

The current authentication implementation has multiple commits scattered across services. Registration and OTP resend can leave partially completed states if one step succeeds and the next fails.

## Decision

A complete application use case owns its database transaction.

Repositories should participate in the current transaction and should not independently commit.

## Examples

### Registration

```text
BEGIN
  create user
  create OTP
COMMIT
```

### Friend acceptance

```text
BEGIN
  validate request
  validate block state
  validate friend limit
  create friendship
  update request
COMMIT
```

## Alternatives Considered

### Repository-level commits
Rejected because repositories cannot know the complete business operation.

### Route-level manual commits
Rejected because transport code should not own business transactions.

## Consequences

### Positive
- Atomic business operations
- Clear rollback semantics
- Easier testing
- Fewer partial-state bugs

### Negative
- Application services need explicit transaction design
- External side effects require careful handling

## Rule

External network calls such as email sending should not keep long-running database transactions open.
