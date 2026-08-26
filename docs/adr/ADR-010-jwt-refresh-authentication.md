# ADR-010: Use JWT Access Tokens with Refresh Tokens

**Status:** Accepted

## Context

TalkTribe already implements JWT-based authentication and refresh-token rotation. The application requires authenticated REST and WebSocket access.

## Decision

Use:

- short-lived JWT access tokens
- longer-lived refresh tokens
- refresh-token rotation
- refresh-token revocation
- logout and logout-all

Email OTP remains the registration verification mechanism for MVP.

## Alternatives Considered

### Server-side session cookies only
Not selected because the current architecture and implementation already use JWT successfully.

### Long-lived access token only
Rejected because revocation and stolen-token risk are worse.

### OAuth-only authentication
Deferred; Google authentication may be added later.

## Consequences

### Positive
- Works well with API clients
- Supports short-lived access authorization
- Refresh-token revocation enables session control

### Negative
- Secret/key management must be correct
- Refresh-token lifecycle adds complexity
- Short-lived access tokens may remain valid until expiry after revocation

## Security Requirements

- one canonical configuration source
- no random production secret fallback
- secure refresh-token storage
- token rotation
- role/account-state authorization
