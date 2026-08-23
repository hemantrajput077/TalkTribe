# ADR-001: Use a Modular Monolith

**Status:** Accepted

## Context

TalkTribe is an early-stage language-exchange platform with a relatively small expected initial user base. The system needs clear boundaries between authentication, profiles, matching, friendship, messaging, presence, calls, and admin functionality, but does not yet need independent deployment of each domain.

## Decision

TalkTribe will use a **modular monolith** for the MVP.

The backend will remain one FastAPI application and one deployable unit, while business capabilities are separated into explicit modules.

## Alternatives Considered

### Traditional layered monolith
Rejected as the long-term structure because global `services/`, `repositories/`, `models/`, and `schemas/` folders become difficult to manage as domains grow.

### Microservices
Rejected for MVP because they add deployment, networking, distributed transaction, observability, and operational complexity without a demonstrated need.

## Consequences

### Positive
- Simpler deployment
- Lower cost
- Easier local development
- Clear business ownership
- Easier transactions
- Can later extract a domain if justified

### Negative
- Requires discipline to enforce module boundaries
- Shared database makes accidental cross-domain access technically possible
- Independent scaling is not available until a domain is extracted

## Follow-up

Reconsider microservices only when a concrete scaling, operational, or organizational requirement justifies them.
