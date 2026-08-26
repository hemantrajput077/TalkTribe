# TalkTribe Authentication Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** Authentication / Identity  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `TARGET_ARCHITECTURE.md`, `SECURITY_ARCHITECTURE.md`, `DATABASE_ARCHITECTURE.md`, `API_ARCHITECTURE.md`

---

# 1. Purpose

This document defines the end-to-end authentication workflow for TalkTribe.

It covers:

- registration
- duplicate validation
- OTP generation
- OTP verification
- account activation
- login
- JWT access tokens
- refresh tokens
- protected requests
- logout
- logout-all
- password reset direction
- account state handling
- failure paths
- security requirements
- transactional boundaries
- implementation dependencies

This workflow describes **how the authentication feature behaves**, not how the files are organized internally.

---

# 2. Authentication Goals

The authentication system must ensure that:

1. only valid users can create accounts
2. email ownership is verified
3. duplicate username/email/phone registration is prevented
4. passwords are never stored in plaintext
5. OTPs expire and cannot be reused
6. unverified accounts cannot use protected application functionality
7. suspended/blocked accounts cannot authenticate normally
8. access tokens are short-lived
9. refresh tokens can be rotated and revoked
10. authenticated identity can be reused by all other TalkTribe domains

---

# 3. Required Registration Fields

Current product decision:

```text
username
email
phone number
password
full name
```

Target rule:

```text
username    → required
email       → required
phone       → required
password    → required
full name   → required
```

Phone is required even though the current implementation may not yet use it.

Reason:

```text
one phone number should not be able to create unlimited accounts
```

and future moderation/account-block rules may use it as part of account identity controls.

---

# 4. Account States

Recommended workflow states:

```text
PENDING_VERIFICATION
ACTIVE
SUSPENDED
BLOCKED
DELETED
```

Primary registration lifecycle:

```text
No Account
   ↓
PENDING_VERIFICATION
   ↓ OTP verified
ACTIVE
```

Admin lifecycle:

```text
ACTIVE
  ├── SUSPENDED
  ├── BLOCKED
  └── DELETED
```

Exact distinction between `SUSPENDED` and `BLOCKED` should remain consistent with Security Architecture.

---

# 5. Registration — Happy Path

```text
User opens registration
        ↓
Enter:
- username
- email
- phone number
- password
- full name
        ↓
POST /api/v1/auth/register
        ↓
API schema validation
        ↓
Check username uniqueness
        ↓
Check email uniqueness
        ↓
Check phone uniqueness
        ↓
Hash password
        ↓
BEGIN TRANSACTION
        ↓
Create user:
status = PENDING_VERIFICATION
is_verified = false
        ↓
Generate OTP
        ↓
Store OTP hash
        ↓
COMMIT
        ↓
Send OTP email
        ↓
Return registration success
        ↓
User sees OTP verification screen
```

---

# 6. Registration Validation

## API-boundary validation

Pydantic should validate:

```text
required fields
email format
username format
password format
full-name format
field lengths
unexpected fields
```

## Application/domain validation

Application layer should validate:

```text
username unique
email unique
phone unique
account registration rules
```

Database constraints provide the final uniqueness guarantee.

---

# 7. Duplicate Registration

Possible conflicts:

```text
username already exists
email already exists
phone already exists
```

Recommended result:

```text
409 Conflict
```

Example error codes:

```text
USERNAME_ALREADY_EXISTS
EMAIL_ALREADY_EXISTS
PHONE_ALREADY_EXISTS
```

Do not depend only on a pre-insert query.

Database unique constraints must also enforce uniqueness.

---

# 8. Registration Transaction Boundary

Registration must not leave a user without a verification record because of partial commits.

Target:

```text
BEGIN
  create user
  create OTP record
COMMIT
```

Then:

```text
send email
```

Do not keep the database transaction open during SMTP/network delivery.

---

# 9. Email Delivery Failure

Possible scenario:

```text
User created
OTP created
database committed
email sending fails
```

The user remains:

```text
PENDING_VERIFICATION
```

They must be able to use:

```text
resend OTP
```

This prevents a stranded account.

API may return a meaningful temporary delivery error while preserving the account state.

Do not delete the user merely because one email attempt failed.

---

# 10. OTP Generation

Current product decision:

```text
OTP required for registration
```

Recommended OTP properties:

```text
6 digits
cryptographically secure generation
purpose-bound
short-lived
single-use
```

Current baseline:

```text
expiry = 5 minutes
maximum verification attempts = 3
```

---

# 11. OTP Storage

Target:

```text
plaintext OTP
   ↓
hash OTP
   ↓
store otp_hash
```

Database should not store the plaintext OTP.

The plaintext value exists only long enough to send it to the user.

---

# 12. OTP Verification — Happy Path

```text
User receives OTP
        ↓
Enter OTP
        ↓
POST /api/v1/auth/verify-email
        ↓
Load user
        ↓
Load latest valid registration OTP
        ↓
Check:
- correct purpose
- unused
- not expired
- attempts remaining
        ↓
Hash submitted OTP
        ↓
Compare hashes
        ↓
BEGIN TRANSACTION
        ↓
Mark OTP used
        ↓
Mark user verified
        ↓
Set account status ACTIVE
        ↓
COMMIT
        ↓
Return verification success
```

---

# 13. Invalid OTP

If submitted OTP does not match:

```text
increment attempt count
        ↓
remaining attempts?
```

If yes:

```text
reject verification
```

If no:

```text
invalidate/lock current OTP
        ↓
require resend after cooldown
```

Recommended error:

```text
INVALID_OTP
```

Do not reveal the correct OTP or internal hash details.

---

# 14. Expired OTP

If:

```text
current time > expires_at
```

then:

```text
OTP cannot be used
```

Return an error such as:

```text
OTP_EXPIRED
```

User can request a new OTP.

---

# 15. OTP Reuse

After successful verification:

```text
is_used = true
```

Any later attempt to use the same OTP must fail.

---

# 16. Resend OTP Workflow

```text
User selects Resend OTP
        ↓
POST /api/v1/auth/resend-otp
        ↓
Validate account
        ↓
Already verified?
   ├── Yes → reject/unnecessary
   └── No
        ↓
Check resend cooldown
        ↓
Check rate limit
        ↓
Invalidate previous active registration OTPs
        ↓
Create new OTP
        ↓
Store hash
        ↓
Commit
        ↓
Send email
        ↓
Return success
```

---

# 17. OTP Resend Abuse Protection

Controls:

```text
per-user/email cooldown
per-IP rate limit
maximum request rate
temporary cooldown after abuse
```

Current product direction:

```text
show popup:
"Try again later."
```

when rate/cooldown limits are exceeded.

---

# 18. Login — Happy Path

```text
User enters username + password
        ↓
POST /api/v1/auth/login
        ↓
Validate input format
        ↓
Load user by username
        ↓
Verify password
        ↓
Check account status
        ↓
Check email verified
        ↓
Create access token
        ↓
Create refresh token
        ↓
Persist refresh-token record/identifier
        ↓
Return token pair
```

---

# 19. Login Failure Cases

## User does not exist

Return:

```text
401
Incorrect username or password
```

## Wrong password

Return the same:

```text
401
Incorrect username or password
```

This prevents useful username enumeration through login responses.

## Email not verified

Return:

```text
403
EMAIL_NOT_VERIFIED
```

## Suspended/blocked account

Return:

```text
403
ACCOUNT_NOT_ALLOWED
```

or a more specific stable error code.

---

# 20. Login Security

Login must include:

- secure password comparison
- generic invalid-credential errors
- rate limiting
- no password logging
- no token logging
- account state validation

Current system's dummy-hash path for nonexistent users may be retained if it helps reduce obvious timing differences.

---

# 21. Access Token

Purpose:

```text
authorize normal protected requests
```

Recommended characteristics:

```text
short-lived
JWT
signed by server
contains user identity
contains token type
contains expiry
contains JTI
```

Likely lifetime:

```text
~15 minutes
```

Exact value remains configurable.

---

# 22. Refresh Token

Purpose:

```text
obtain a new access token without full login
```

Characteristics:

```text
longer-lived
revocable
rotated
server-side tracked
```

Suggested flow:

```text
refresh token
   ↓
verify signature/type
   ↓
verify DB record
   ↓
not expired?
   ↓
not revoked?
   ↓
revoke/rotate old token
   ↓
create new access token
   ↓
create new refresh token
   ↓
persist new token identifier
   ↓
return new pair
```

---

# 23. Refresh Endpoint

```text
POST /api/v1/auth/refresh
```

Failure cases:

```text
invalid token
wrong token type
expired token
revoked token
user no longer active
```

All must reject refresh.

---

# 24. Protected Request Workflow

Example:

```text
GET /api/v1/profiles/me
        ↓
Authorization: Bearer <access-token>
        ↓
API authentication dependency
        ↓
Verify token
        ↓
Resolve user ID
        ↓
Check account status
        ↓
AuthenticatedIdentity
        ↓
Profile application service
```

Other domains use the resolved identity.

They should not reimplement JWT verification themselves.

---

# 25. Authenticated Identity Contract

Other domains should receive a small trusted object such as:

```text
AuthenticatedIdentity
├── user_id
├── role
├── account_status
└── is_verified
```

They should not receive:

```text
password hash
OTP records
refresh-token records
JWT secret
```

---

# 26. Logout

```text
POST /api/v1/auth/logout
```

Flow:

```text
authenticated user
   ↓
identify refresh/session token
   ↓
mark token revoked
   ↓
return 204
```

Access token may remain valid until short expiry unless an access-token denylist is later introduced.

---

# 27. Logout All

```text
POST /api/v1/auth/logout-all
```

Flow:

```text
authenticated user
   ↓
revoke all active refresh tokens for user
   ↓
return 204
```

Use cases:

```text
security concern
password reset
user intentionally signs out everywhere
```

---

# 28. Password Reset — Future/Required Account Capability

Current product decision:

```text
forgot password should allow password reset after email ownership verification
```

Target flow:

```text
User selects Forgot Password
        ↓
Enter email
        ↓
request reset OTP
        ↓
generic response
        ↓
receive OTP
        ↓
verify OTP
        ↓
set new password
        ↓
hash password
        ↓
revoke all refresh tokens
        ↓
return success
```

Google authentication may be considered later.

---

# 29. Account Deletion Authentication

Current product decision:

```text
account holder can delete their account
all data should be erased
new registration later creates a new account
```

Before deletion:

```text
authenticated owner
+
strong confirmation
```

Recommended:

```text
password re-entry or recent-auth confirmation
```

Admin deletion follows separate privileged authorization rules.

Exact retention conflict with audit/report records remains open.

---

# 30. Admin Authentication

Admin uses the same authentication mechanism.

Difference:

```text
role = ADMIN
```

Admin route:

```text
authenticate
   ↓
require_admin
   ↓
admin application service
```

Frontend admin UI is not a security boundary.

Backend authorization is mandatory.

---

# 31. Auth API Surface

Current/target:

```text
POST /api/v1/auth/register
POST /api/v1/auth/verify-email
POST /api/v1/auth/resend-otp
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/logout-all
GET  /api/v1/auth/me
```

Future:

```text
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
POST /api/v1/auth/change-password
```

---

# 32. Auth Domain Data

Main durable records:

```text
users
otps
refresh_tokens
```

Target user security fields:

```text
id
username
email
phone_number
password_hash
role
account_status
is_verified
created_at
updated_at
```

---

# 33. Current Implementation → Target Workflow

Already implemented:

```text
registration
OTP
verification
login
JWT
refresh token
logout
logout-all
/me
```

Before building more features, the existing behavior should be hardened rather than rewritten.

Recommended sequence:

```text
1. Add automated tests
2. Remove/protect insecure development endpoints
3. Consolidate configuration
4. Consolidate DB/session infrastructure
5. Consolidate password/security implementation
6. Fix JWT secret configuration
7. Hash OTP
8. Restore/fix OTP DB constraints/indexes
9. Add phone + role/account status as required
10. Move route orchestration to Auth application service
11. Establish consistent repositories
12. Fix transaction ownership
13. Add rate limiting
14. Preserve existing API behavior wherever practical
```

---

# 34. Auth Error Codes

Recommended stable error codes:

```text
USERNAME_ALREADY_EXISTS
EMAIL_ALREADY_EXISTS
PHONE_ALREADY_EXISTS
INVALID_CREDENTIALS
EMAIL_NOT_VERIFIED
INVALID_OTP
OTP_EXPIRED
OTP_ATTEMPTS_EXCEEDED
OTP_RESEND_RATE_LIMITED
ACCOUNT_SUSPENDED
ACCOUNT_BLOCKED
INVALID_ACCESS_TOKEN
INVALID_REFRESH_TOKEN
REFRESH_TOKEN_REVOKED
AUTHENTICATION_REQUIRED
```

The final catalog may be centralized.

---

# 35. Security Events

Important events to log safely:

```text
registration attempt/success
OTP verification success/failure
OTP resend rate limit
login success/failure
refresh-token rotation
logout
logout-all
account suspension
account block
password reset
```

Do not log:

```text
password
OTP
access token
refresh token
JWT secret
```

---

# 36. Testing Workflow

Before marking Auth complete:

## Registration

```text
valid registration
duplicate username
duplicate email
duplicate phone
invalid password
email delivery failure recovery
```

## OTP

```text
valid OTP
wrong OTP
expired OTP
used OTP
attempt limit
resend cooldown
new OTP invalidates old OTP
```

## Login

```text
valid login
wrong password
unknown user
unverified account
suspended account
blocked account
```

## Tokens

```text
access token validation
refresh success
refresh rotation
revoked refresh token rejected
expired refresh token rejected
logout
logout-all
```

## Authorization

```text
missing token
invalid token
regular user cannot access admin endpoint
```

---

# 37. Definition of Done — Authentication

Authentication is considered architecturally ready for dependent features when:

- [ ] Registration works.
- [ ] Username/email/phone uniqueness is enforced.
- [ ] Password is securely hashed.
- [ ] OTP is stored hashed.
- [ ] OTP expiry works.
- [ ] OTP attempts are limited.
- [ ] OTP resend is rate limited.
- [ ] Email failure can be recovered with resend.
- [ ] Verification activates the account.
- [ ] Unverified account cannot login.
- [ ] Access token works.
- [ ] Refresh token rotation works.
- [ ] Logout works.
- [ ] Logout-all works.
- [ ] Suspended/blocked users are rejected.
- [ ] USER/ADMIN roles exist.
- [ ] Insecure development user endpoints are removed/protected.
- [ ] Transaction boundaries are consistent.
- [ ] Configuration/security implementation is canonical.
- [ ] Auth tests pass.
- [ ] API schemas do not expose secrets.
- [ ] Authenticated identity contract is available to other domains.

---

# 38. Dependencies on Authentication

Authentication is foundational for:

```text
Profile
Language
Matching
Friendship
Messaging
Presence
Pairing
Voice Calls
Admin
Reports
```

Therefore Auth must be stabilized before the rest of the MVP is built aggressively.

---

# 39. Authentication Workflow Diagram

```text
                         NEW USER
                            │
                            ▼
                       REGISTER
                            │
                   validate uniqueness
                            │
                            ▼
                     HASH PASSWORD
                            │
                            ▼
                 CREATE USER + OTP
                      (transaction)
                            │
                            ▼
                       SEND EMAIL
                            │
                            ▼
                      VERIFY OTP
                            │
                            ▼
                    ACCOUNT ACTIVE
                            │
                            ▼
                          LOGIN
                            │
                            ▼
                ACCESS + REFRESH TOKEN
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
      PROTECTED REQUEST              TOKEN REFRESH
              │                           │
              │                           ▼
              │                      ROTATE TOKEN
              │
              ▼
        OTHER DOMAINS
```

---

# 40. Next Workflow

After Authentication:

```text
AUTHENTICATION_WORKFLOW.md      ✅
        ↓
PROFILE_WORKFLOW.md             ← NEXT
        ↓
LANGUAGE_WORKFLOW.md
        ↓
MATCHING_WORKFLOW.md
        ↓
FRIENDSHIP_WORKFLOW.md
        ↓
PRESENCE_WORKFLOW.md
        ↓
PAIRING_WORKFLOW.md
        ↓
VOICE_CALL_WORKFLOW.md
        ↓
MESSAGING_WORKFLOW.md
        ↓
FEEDBACK_REPORTING_WORKFLOW.md
        ↓
ADMIN_WORKFLOW.md
        ↓
FEATURE_DEPENDENCIES.md
        ↓
DEVELOPMENT_ROADMAP.md
        ↓
JIRA
```
