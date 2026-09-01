# ADR-003: Use PostgreSQL as the Primary Durable Store

**Status:** Accepted

## Context

TalkTribe stores relational and durable data such as users, profiles, languages, friendships, conversations, messages, call metadata, reports, and admin records.

## Decision

Use **PostgreSQL** as the primary durable system of record.

SQLAlchemy is used for ORM/database access and Alembic for schema migrations.

## Alternatives Considered

### MongoDB / document database
Rejected because the data model is strongly relational and benefits from foreign keys, constraints, and transactions.

### Redis as primary storage
Rejected because Redis is intended for transient realtime state.

### Separate database per domain
Rejected for MVP because it adds unnecessary operational complexity.

## Consequences

### Positive
- Strong relational integrity
- Transactions
- Mature indexing/query capabilities
- Good support in FastAPI/SQLAlchemy ecosystem

### Negative
- Shared database requires architectural discipline
- Large-scale messaging may require partitioning or archival later

## Rule

PostgreSQL stores durable truth. Redis or caches must never be the only copy of durable business records.
