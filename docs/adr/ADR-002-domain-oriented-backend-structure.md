# ADR-002: Organize Backend by Business Domain

**Status:** Accepted

## Context

The earlier project structure used global technical folders such as services, repositories, models, and schemas. As more features are added, this makes ownership unclear and creates coupling across unrelated business areas.

## Decision

Backend business code will be organized primarily by **domain/capability**.

Target modules include:

- auth
- profile
- language
- matching
- friendship
- messaging
- presence
- calls
- admin

Each domain may contain its own API, application, domain, infrastructure, and schema components.

## Alternatives Considered

### Global technical-layer folders
Rejected as the primary organization because it scales poorly in maintainability.

### Fully independent services
Rejected for MVP because separate deployments are unnecessary.

## Consequences

### Positive
- Business ownership is clearer
- Related files are colocated
- Easier onboarding
- Easier later extraction of a module
- Reduces accidental coupling

### Negative
- Some shared infrastructure still needs central organization
- Developers must understand domain ownership before adding code

## Rule

A file should first be placed according to **which domain owns the behavior**, then according to its internal technical layer.
