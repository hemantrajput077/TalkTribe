# TalkTribe Security Architecture

**Status:** Stage 2 architecture design  
**Architecture style:** Modular Monolith  
**Scope:** MVP security, authentication, authorization, abuse prevention, secrets, data protection, admin security, and operational security  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `DOMAIN_BOUNDARIES.md`, `COMPONENT_ARCHITECTURE.md`, `DATABASE_ARCHITECTURE.md`, `API_ARCHITECTURE.md`

---

# 1. Purpose

This document defines the TalkTribe security architecture for MVP.

It answers:

- How users authenticate
- How roles and permissions work
- How admin access is protected
- How resource ownership is enforced
- How blocked users are restricted
- How OTP/JWT/password security should work
- How rate limiting and abuse protection work
- How secrets are managed
- What data may be exposed
- How logging and audit should work
- Which current security issues must be fixed before adding major features

Security is treated as an architectural concern, not as route-by-route patching.

---

# 2. Security Principles

1. Deny access by default.
2. Authenticate before protected actions.
3. Authorize every sensitive action explicitly.
4. Keep business authorization in application/domain services, not only routes.
5. Apply least privilege.
6. Never trust client-provided identity or role claims without verification.
7. Never expose authentication secrets or internal security state.
8. Protect abuse-sensitive endpoints with rate limiting.
9. Store passwords and OTPs securely.
10. Keep secrets outside source control.
11. Use HTTPS in production.
12. Audit privileged admin actions.
13. Blocked-user rules must be enforced consistently across domains.
14. Security-sensitive behavior must be covered by automated tests.
15. Avoid silent security fallbacks.

---

# 3. Security Boundaries

TalkTribe has multiple security boundaries:

```text
Internet
   ↓
Reverse Proxy / HTTPS
   ↓
FastAPI API / WebSocket Transport
   ↓
Authentication
   ↓
Authorization
   ↓
Application / Domain Rules
   ↓
Repositories / Infrastructure
   ↓
PostgreSQL / Redis / External Services
```

Every boundary should validate only what it owns.

---

# 4. Identity and Roles

Initial MVP roles:

```text
USER
ADMIN
```

The authenticated identity should include enough information to make authorization decisions, for example:

```text
user_id
role
account_status
is_verified
```

Do not trust user-supplied role values in requests.

Role information must come from trusted server-side state or a verified token tied to trusted state.

---

# 5. Account States

Recommended account lifecycle states:

```text
PENDING_VERIFICATION
ACTIVE
SUSPENDED
BLOCKED
DELETED
```

Exact enum values can be adjusted, but security-sensitive decisions must not rely only on a single ambiguous boolean such as `is_active`.

### Example behavior

| State | Login | Use App | View Profiles | Message/Call |
|---|---:|---:|---:|---:|
| PENDING_VERIFICATION | No | No | No | No |
| ACTIVE | Yes | Yes | Yes | Yes |
| SUSPENDED | No/limited | No/limited | No | No |
| BLOCKED | No | No | No | No |
| DELETED | No | No | No | No |

The final behavior of `SUSPENDED` vs `BLOCKED` must be defined in Admin policy.

---

# 6. Authentication Architecture

Authentication answers:

> Who is making this request?

Current mechanism:

```text
Registration
   ↓
Email OTP verification
   ↓
Login
   ↓
JWT access token
   ↓
Refresh token
```

The authentication system should support:

- registration
- email verification
- login
- access token
- refresh token
- logout
- logout-all
- password reset later
- account verification state

---

# 7. Password Security

Passwords must:

- never be stored in plaintext
- be hashed with one canonical password-hashing implementation
- use a modern password hashing scheme
- be compared using secure library functions
- never be logged
- never be returned through API responses

Current code has duplicated password hashing utilities/libraries.

Target direction:

```text
one canonical security module
one password hashing implementation
```

Remove duplicate unused password-hashing code.

### Password policy

The current app already enforces password complexity rules.

Security architecture should keep validation consistent between registration/password reset/change flows.

Do not enforce username-reserved-word rules on login input.

---

# 8. OTP Security

Current implementation stores OTP in plaintext.

Target direction:

```text
generate OTP
   ↓
send plaintext OTP to user
   ↓
store only hashed OTP representation
   ↓
verify by hashing submitted OTP
```

OTP policy should include:

```text
expiry
attempt limit
resend cooldown
single-use
purpose binding
rate limiting
```

Current product decisions indicate:

```text
OTP expiry ≈ 5 minutes
maximum attempts ≈ 3
```

These values should be treated as the current product baseline unless changed later.

OTP must be purpose-specific.

Examples:

```text
REGISTRATION
PASSWORD_RESET
EMAIL_CHANGE
```

A registration OTP must not be accepted for password reset.

---

# 9. OTP Abuse Prevention

Protect:

```text
/register
/verify-email
/resend-otp
```

Controls should include:

- per-IP rate limit
- per-email/user rate limit
- resend cooldown
- verification attempt limit
- generic responses where enumeration risk exists

After too many attempts:

```text
temporary block/cooldown
```

Do not permanently lock a user simply because an attacker guessed OTPs against their email.

---

# 10. JWT Architecture

Use:

```text
short-lived access token
longer-lived refresh token
```

JWT payload may include:

```text
sub
type
jti
iat
exp
role   # optional, if carefully handled
```

Do not include sensitive personal data in JWTs.

### Important

The current audit found two configuration systems with inconsistent secret names.

This must be fixed.

There should be one canonical configuration source for:

```text
ACCESS_TOKEN_SECRET
REFRESH_TOKEN_SECRET
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS
```

No randomly generated production secret should silently be used as a default.

Production should fail fast if required secrets are missing.

---

# 11. Access Token Policy

Recommended MVP direction:

```text
Access token lifetime: short
```

Current code has differing defaults around 15/30 minutes.

Choose one canonical value during implementation.

A reasonable MVP default is around:

```text
15 minutes
```

but this remains a technical configuration decision.

---

# 12. Refresh Token Policy

Refresh tokens should support:

- expiration
- revocation
- rotation
- logout
- logout-all
- server-side validity checks

Prefer storing:

```text
hashed token
or
secure token identifier/JTI
```

instead of raw token values where practical.

On refresh:

```text
validate token
   ↓
verify not expired
   ↓
verify not revoked
   ↓
rotate token
   ↓
revoke old token
   ↓
issue new token pair
```

---

# 13. Authentication Dependency

Transport-level authentication belongs in API dependencies.

Recommended:

```text
app/api/dependencies.py
```

Examples:

```text
get_current_identity()
require_authenticated_user()
require_admin()
```

These should delegate token verification to the Auth/security components.

Future modules should not import `auth_service.py` just to authenticate requests.

---

# 14. Authorization Architecture

Authorization answers:

> Is this authenticated user allowed to perform this action?

Authorization must be enforced at two levels:

### Route/API gate

Example:

```text
require authenticated user
require admin
```

### Application/domain authorization

Example:

```text
Can user A view profile B?
Can user A message B?
Can user A start a call with B?
Can user A accept this friend request?
```

Business authorization must not live only in route decorators/dependencies.

---

# 15. Authorization Matrix

Initial MVP baseline:

| Action | USER | ADMIN |
|---|---:|---:|
| Register/login | Yes | Yes |
| View own profile | Yes | Yes |
| Edit own profile | Yes | Yes |
| View another authenticated user's allowed profile | Yes | Yes |
| Edit another user's profile | No | Only if explicit admin feature |
| Send friend request | Yes | Not a special admin capability |
| Accept/reject own incoming request | Yes | No special bypass |
| Block another user | Yes | No special bypass |
| Message eligible user | Yes | No special bypass |
| Start voice call with eligible user | Yes | No special bypass |
| View own conversations | Yes | No |
| List all users | No | Yes |
| Suspend user | No | Yes |
| Resolve reports | No | Yes |
| Perform moderation | No | Yes |
| Delete another user | No | Only if explicitly allowed |
| View auth secrets | No | No |

Admins should not automatically receive unrestricted access to private message content unless the moderation requirements explicitly require it.

---

# 16. Resource Ownership

Ownership must be explicit.

Examples:

```text
Profile owner
Conversation participant
Message sender
Friend request receiver/sender
Call participant
Report creator
```

Authorization must verify ownership/participation before returning or modifying data.

Example:

```text
GET /conversations/{id}
        ↓
Is current user a participant?
        ↓
Yes → allowed
No  → denied
```

---

# 17. Profile Visibility

Final product decision:

> Any authenticated co-learner and admin may view another user's permitted profile.

Therefore:

```text
unauthenticated → denied
authenticated user → allowed to view permitted public/profile fields
admin → allowed according to admin policy
```

This does not mean every stored user field is public.

Never expose through normal profile APIs:

- email unless product explicitly requires it
- phone number
- password hash
- OTP data
- refresh tokens
- internal moderation notes
- internal security state

Use a dedicated `PublicProfileResponse`.

---

# 18. Messaging Authorization

Friendship is not strictly required before messaging.

Therefore messaging permission must be determined by explicit rules.

At minimum:

```text
authenticated sender
target exists
both accounts active
no blocking relationship
messaging preference allows contact
```

If user preference allows:

```text
friends only
```

then Friendship must confirm friendship.

If preference allows:

```text
any eligible user
```

then friendship is not required.

Messaging application service owns this decision.

---

# 19. Blocking Rules

Current product decision:

> A blocked user cannot do anything toward the blocker until unblocked.

Therefore blocking must affect:

```text
profile interaction
friend requests
messages
voice calls
matching/discovery where appropriate
```

Recommended rule:

If A blocks B:

```text
B cannot message A
B cannot call A
B cannot send friend request to A
B should not be recommended to A
A and B should not be matched together
```

Exact profile visibility after block remains a product/security detail.

### Existing conversations

Current decision:

```text
conversation history stays
new message exchange is disabled
```

This rule must be enforced in Messaging.

---

# 20. Voice Call Authorization

Before creating/accepting a call:

```text
caller authenticated
callee exists
both accounts active
no block relationship
callee available/online according to call rules
caller permitted to call callee
rate limit not exceeded
```

Backend must authorize call signaling.

The frontend must never be able to initiate unrestricted WebRTC signaling directly to arbitrary users without backend checks.

---

# 21. Admin Security

Admin is MVP and requires stronger controls.

At minimum:

```text
ADMIN role
authenticated session
action-level authorization
audit logging
```

Recommended admin-sensitive operations:

```text
list users
view user moderation state
suspend/activate user
resolve reports
platform block where implemented
delete user only if explicitly permitted
```

### Never

- expose admin operations without authentication
- infer admin based on frontend route/UI
- let client send `role=ADMIN`
- put admin privileges in unverified request body
- bypass domain rules by importing every repository directly

---

# 22. Admin Audit Logging

Sensitive admin actions should generate audit records.

Recommended data:

```text
admin_user_id
action
target_type
target_id
timestamp
metadata
request_id
```

Examples:

```text
USER_SUSPENDED
USER_REACTIVATED
REPORT_RESOLVED
USER_DELETED
```

Audit records should be protected from normal users.

---

# 23. Rate Limiting

Redis is the preferred MVP backend for rate limiting.

High-priority endpoints/events:

```text
register
login
verify OTP
resend OTP
friend request
message send
voice-call initiate
report submission
admin-sensitive actions
```

Possible scopes:

```text
per IP
per user
per email/username
per target user
```

Example conceptual policy:

```text
login attempts → per account + IP
OTP resend → per user/email
friend requests → per user
calls → per caller/target
messages → per sender
```

Exact numbers belong in implementation/security configuration.

---

# 24. Brute Force / Enumeration Protection

Avoid revealing unnecessary account existence.

Example:

For forgot-password:

```text
"If an account exists for this email, instructions have been sent."
```

Registration duplicate handling may still need explicit conflict responses for UX, but sensitive auth flows should be evaluated for enumeration risk.

Login should return a generic error:

```text
Incorrect username or password
```

not:

```text
username exists but password is wrong
```

---

# 25. Input Security

Use Pydantic for boundary validation.

Protect against:

- oversized payloads
- malformed input
- invalid enum values
- unexpected fields
- dangerous file uploads
- path injection
- abusive message/report content

SQLAlchemy parameterization should be used consistently.

Do not build SQL queries through raw string concatenation using user input.

---

# 26. File Upload Security

Profile images should:

- restrict file type
- restrict maximum size
- validate content type
- preferably inspect actual file signature
- generate server-side object keys
- avoid trusting original file names
- avoid storing executable content in web-accessible locations

Store only object metadata/reference in PostgreSQL.

Use object storage for actual images.

---

# 27. Message Content Security

MVP chat rule states no abusive/unethical content.

Architecture should support moderation/reporting without assuming perfect automated moderation.

At minimum:

- users can report another user
- admins can review reports according to MVP admin scope
- message/report payload size limits exist
- dangerous HTML/script content should not be rendered unsafely by frontend

If messages are rendered as plain text, escape/sanitize appropriately on the frontend.

---

# 28. Voice/Realtime Security

Realtime channels must authenticate the user.

WebSocket connection:

```text
connect
   ↓
authenticate token/session
   ↓
bind connection to server-side user ID
```

Never trust:

```text
{"user_id": 123}
```

from the client as proof of identity.

For realtime events:

```text
message.send
call.start
call.offer
call.answer
```

the server must derive sender identity from the authenticated connection.

---

# 29. WebSocket Authorization

Each event still requires authorization.

Example:

```text
call.offer
   ↓
authenticated socket user
   ↓
is user a participant in this active call?
   ↓
yes → relay
no → reject
```

Authentication at connection time does not eliminate event-level authorization.

---

# 30. Redis Security

Redis stores transient security/realtime state.

Requirements:

- not publicly exposed to the internet
- protected by network/firewall rules
- authentication/TLS when provider requires/supports it
- secrets stored in environment/secret manager
- keys should not contain sensitive plaintext unnecessarily
- TTL for temporary keys
- no durable auth secrets stored without reason

If Redis is unavailable:

```text
durable user/message data must remain intact
```

---

# 31. PostgreSQL Security

Production PostgreSQL should:

- not be publicly open unnecessarily
- use strong credentials
- use least-privilege application user
- use encrypted provider connection/TLS where applicable
- use backups
- separate test/dev/prod databases
- avoid using admin/superuser DB credentials for application runtime

Logs must not reveal credentials or sensitive query data.

---

# 32. Secrets Management

Initial low-cost deployment:

```text
environment variables on EC2
```

Future:

```text
AWS SSM Parameter Store
AWS Secrets Manager
```

Secrets include:

```text
JWT access secret
JWT refresh secret
database credentials
Redis credentials
SMTP credentials
storage credentials
TURN credentials
```

Never:

- commit `.env`
- put real secrets in `.env.example`
- print secrets during startup
- include secrets in frontend bundles

---

# 33. HTTPS

Production traffic must use HTTPS.

Initial direction:

```text
Nginx
+
Let's Encrypt / Certbot
```

or equivalent TLS termination.

Redirect HTTP → HTTPS.

WebSocket should use:

```text
wss://
```

in production.

---

# 34. CORS

CORS must be environment-specific.

Development may allow local frontend origins.

Production should allow only approved origins such as the deployed frontend.

Avoid:

```text
allow_origins=["*"]
```

when credentials/authenticated browser requests are used.

---

# 35. Security Headers

At reverse-proxy/application level, consider:

```text
Strict-Transport-Security
X-Content-Type-Options
Content-Security-Policy
Referrer-Policy
X-Frame-Options / frame-ancestors
```

Frontend security policy should be compatible with WebSocket/WebRTC requirements.

---

# 36. Logging Security

Never log:

- plaintext password
- OTP
- access token
- refresh token
- JWT secret
- SMTP password
- full sensitive request body
- raw authorization header

Safe logging examples:

```text
user_id
request_id
endpoint
status
duration
event type
security outcome
```

Security events worth logging:

```text
login success/failure
OTP lockout/rate limit
admin action
account suspension
token revocation
authorization denial
```

---

# 37. Error Security

Errors should be useful without exposing internals.

Client:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Incorrect username or password."
  }
}
```

Server logs may include additional diagnostic information.

Do not expose:

```text
stack traces
SQL
secret values
internal file paths
provider credentials
```

in production responses.

---

# 38. Data Privacy

Sensitive account fields:

```text
email
phone number
authentication/security state
```

should not be exposed to normal co-learners unless a product requirement explicitly says so.

Public/authenticated profile fields should be defined separately.

Potential profile fields visible to co-learners:

```text
display/full name
username
profile photo
bio
profession
location
interests
language/proficiency
rating/stats as product allows
```

Exact field list must be finalized before Profile API implementation.

---

# 39. Account Deletion Security

Current product decision:

> User deletion erases all data.

Deletion must require strong authorization.

For self-deletion:

```text
authenticated account owner
+
recent authentication / password confirmation recommended
```

For admin deletion:

```text
ADMIN
+
explicit privileged permission
+
audit record
```

Because abuse reports/admin audit may need retention, final deletion vs anonymization policy remains an open requirement.

Do not implement destructive cascading deletion until this is resolved.

---

# 40. Session Revocation

Security events that should revoke sessions:

```text
password reset
account suspension
account blocked
manual logout-all
security-sensitive account change
```

Recommended:

```text
revoke all refresh tokens
```

Access tokens are short-lived and may remain valid until expiry unless a token-denylist strategy is introduced.

MVP can accept short-lived access-token expiry instead of maintaining a full access-token denylist.

---

# 41. Security Testing

Required automated tests:

## Authentication

- password hashing
- register
- OTP expiry
- OTP wrong attempt
- OTP reuse prevention
- login invalid credentials
- unverified login
- suspended account login
- refresh rotation
- revoked refresh token
- logout/logout-all

## Authorization

- unauthenticated access denied
- user cannot perform admin operation
- user cannot edit another profile
- non-participant cannot access conversation
- blocked user cannot message
- blocked user cannot call
- non-participant cannot manipulate call

## Admin

- regular user denied
- admin permitted
- privileged action audited

## Rate Limiting

- repeated login/OTP/call requests limited
- expected 429 response

## Data Exposure

- password hash not in API
- OTP not in API
- refresh token records not leaked
- private account fields not present in public profile response

---

# 42. Current Security Problems to Fix Now

Before significant new features:

## Critical

1. Remove/protect unauthenticated list-all-users endpoint.
2. Remove/protect unauthenticated delete-user endpoint.
3. Ensure all privileged user operations require authorization.

## High

4. Consolidate JWT/configuration system.
5. Remove random/default production signing secrets.
6. Hash OTP values.
7. Add rate limiting to auth/OTP endpoints.
8. Fix transaction boundaries in registration/OTP flows.
9. Establish automated auth/security tests.
10. Canonicalize password/security implementation.

## Medium

11. Move auth dependencies to API boundary.
12. Introduce consistent authorization errors.
13. Disable production SQL `echo=True`.
14. Remove dead duplicate security/config/database code.
15. Abstract external email delivery enough for testing.

---

# 43. Security Changes That Can Wait

Can be introduced when the relevant feature arrives:

```text
message rate limits
call rate limits
WebSocket event authorization
TURN credential policy
profile image upload hardening
admin audit logs
report moderation controls
advanced anomaly detection
```

These should not be forgotten, but they do not require premature implementation before their feature exists.

---

# 44. Security Review Before Feature Merge

For every new feature, ask:

```text
Who can call this?
Who owns the resource?
What if the caller is blocked?
What if the account is suspended?
What data is returned?
Could this expose private data?
Could this be abused repeatedly?
Does it need rate limiting?
Does it modify another domain?
Does it require audit logging?
Are security tests present?
```

---

# 45. MVP Security Baseline

Minimum MVP security should include:

```text
secure password hashing
email verification
hashed OTP
short-lived access token
rotating/revocable refresh token
role-based ADMIN protection
resource ownership checks
block enforcement
rate limiting
HTTPS/WSS
protected secrets
safe logging
consistent authorization
automated security tests
admin audit for sensitive actions
database backups
```

---

# 46. Open Security Decisions

Still to finalize:

1. Exact access-token lifetime.
2. Exact refresh-token lifetime.
3. Exact OTP resend cooldown.
4. Exact rate-limit values.
5. Exact `SUSPENDED` vs `BLOCKED` semantics.
6. Exact public profile field list.
7. Messaging privacy preference model.
8. Whether admins can inspect message content for moderation.
9. Account deletion vs moderation/audit retention.
10. Whether sensitive operations require password re-entry.
11. TURN credential strategy.
12. Production OpenAPI documentation exposure.
13. Exact audit-log retention.

---

# 47. Next Architecture Artifact

```text
REQUIREMENTS_BASELINE.md       ✅
DOMAIN_BOUNDARIES.md           ✅
COMPONENT_ARCHITECTURE.md      ✅
DATABASE_ARCHITECTURE.md       ✅
API_ARCHITECTURE.md            ✅
SECURITY_ARCHITECTURE.md       ✅
        ↓
REALTIME_ARCHITECTURE.md       ← NEXT
        ↓
TARGET_ARCHITECTURE.md
        ↓
ADR/*
        ↓
Application Workflows
        ↓
Feature Dependency Map
        ↓
Development Roadmap
        ↓
Epics / Stories / Tasks
        ↓
Jira
```
