# TalkTribe Admin Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** Admin / Moderation  
**Depends on:** `AUTHENTICATION_WORKFLOW.md`, `SECURITY_ARCHITECTURE.md`, `FEEDBACK_REPORTING_WORKFLOW.md`, `TARGET_ARCHITECTURE.md`

---

# 1. Purpose

This document defines the MVP Admin workflow.

It covers:

- admin authentication/authorization
- user listing and inspection
- report review
- account suspension/activation
- platform blocking where applicable
- deletion rules
- audit logging
- cross-domain boundaries
- security
- testing
- Definition of Done

Admin is part of MVP.

---

# 2. Admin Goals

Admin exists to support:

```text
user moderation
report handling
account management
platform safety
```

Admin is not:

```text
a god module
a repository bypass
a way to expose private data casually
```

---

# 3. Admin Role

Initial roles:

```text
USER
ADMIN
```

Admin uses the same authentication system.

Authorization requires:

```text
authenticated
role = ADMIN
account ACTIVE
```

Frontend admin UI is not a security boundary.

---

# 4. Admin Entry Flow

```text
Admin logs in
   ↓
JWT/session created
   ↓
Admin opens admin interface
   ↓
GET /api/v1/admin/...
   ↓
authenticate
   ↓
require ADMIN
   ↓
application-level permission
```

---

# 5. User List

Recommended:

```text
GET /api/v1/admin/users
```

Paginated.

Possible filters:

```text
status
username
email
report state
```

Only approved admin fields should be returned.

---

# 6. User Detail

Recommended:

```text
GET /api/v1/admin/users/{user_id}
```

May include:

```text
account identity summary
profile summary
account status
verification status
moderation/report summary
created_at
```

Do not include:

```text
password hash
OTP
raw refresh tokens
JWT secrets
```

---

# 7. Report Queue

Recommended:

```text
GET /api/v1/admin/reports
```

Filters:

```text
OPEN
UNDER_REVIEW
RESOLVED
DISMISSED
```

Admin can open a report and inspect approved context.

---

# 8. Report Review

```text
Admin opens report
        ↓
validate ADMIN
        ↓
load report
        ↓
load approved user/context information
        ↓
status may become UNDER_REVIEW
        ↓
admin decides:
- resolve without action
- dismiss
- suspend user
- other approved moderation action
```

---

# 9. Resolve Report

Recommended:

```text
POST /api/v1/admin/reports/{id}/resolve
```

Flow:

```text
verify admin
   ↓
verify report actionable
   ↓
record resolution
   ↓
status → RESOLVED
   ↓
audit action
```

---

# 10. Dismiss Report

If report is not actionable:

```text
status → DISMISSED
```

Audit the action.

Do not delete report merely because it was dismissed.

---

# 11. Suspend User

Recommended:

```text
POST /api/v1/admin/users/{id}/suspend
```

Flow:

```text
Admin
   ↓
validate target
   ↓
ensure target action allowed
   ↓
BEGIN
   update account status
   revoke refresh tokens
COMMIT
   ↓
disconnect active sockets
   ↓
remove presence/pairing state
   ↓
audit
```

---

# 12. Suspension Effects

Suspended user should not:

```text
login normally
refresh sessions
remain online
enter pairing
message
start calls
use protected app functionality
```

Exact read-only behavior, if any, remains a policy choice.

---

# 13. Reactivate User

Recommended:

```text
POST /api/v1/admin/users/{id}/activate
```

Flow:

```text
validate ADMIN
   ↓
validate account can be reactivated
   ↓
status → ACTIVE
   ↓
audit
```

User must authenticate again.

---

# 14. Platform Block vs User Block

Do not confuse:

## User Block

```text
A blocks B
```

Owned by Friendship.

## Platform/Admin Block

```text
Admin disables an account from the platform
```

Owned through Auth/Admin account moderation.

These have different meanings and storage.

---

# 15. Admin Delete User

Deletion is a destructive operation.

If supported:

```text
DELETE /api/v1/admin/users/{id}
```

must require:

```text
ADMIN
explicit authorization
strong confirmation
audit
```

Current user decision says account deletion erases all user data.

However audit/report retention may conflict with total deletion.

Therefore admin hard-delete should not be implemented until retention policy is finalized.

---

# 16. Self-Protection Rules

Admin workflow should prevent accidental dangerous operations such as:

```text
admin deleting own active account unexpectedly
admin suspending themselves
last-admin removal
```

Exact policies depend on how many admins exist.

At minimum, sensitive self-actions should be deliberate.

---

# 17. Cross-Domain Access

Admin should use explicit contracts.

Allowed:

```text
Admin → UserManagement
Admin → ReportManagement
Admin → ProfileModerationReader
```

Forbidden:

```text
Admin → every repository directly
```

---

# 18. Admin and Profile

Admin may need to view:

```text
public profile
profile details relevant to moderation
```

Admin does not automatically own Profile business logic.

Profile changes by Admin require an explicit moderation use case.

---

# 19. Admin and Messages

Whether Admin may read private message content is **not finalized**.

Do not implement broad message surveillance by default.

If moderation requires content access:

```text
define explicit policy
define audit
define scope
define retention
```

first.

---

# 20. Admin and Calls

Voice media is not recorded.

Admin may inspect call metadata if required:

```text
participants
timestamps
duration
status
related report
```

No raw voice recording exists in MVP architecture.

---

# 21. Admin Audit Log

Sensitive actions should create audit records.

Recommended:

```text
admin_user_id
action
target_type
target_id
metadata
created_at
request_id
```

Examples:

```text
USER_SUSPENDED
USER_ACTIVATED
REPORT_RESOLVED
REPORT_DISMISSED
USER_DELETED
```

---

# 22. Audit Requirements

Audit log should be:

```text
append-oriented
admin-only
protected from normal users
```

Do not log secrets or unnecessary private data.

---

# 23. API Surface

Recommended MVP:

```text
GET  /api/v1/admin/users
GET  /api/v1/admin/users/{id}
POST /api/v1/admin/users/{id}/suspend
POST /api/v1/admin/users/{id}/activate

GET  /api/v1/admin/reports
GET  /api/v1/admin/reports/{id}
POST /api/v1/admin/reports/{id}/resolve
POST /api/v1/admin/reports/{id}/dismiss
```

Possible later:

```text
DELETE /api/v1/admin/users/{id}
```

after deletion/retention rules are finalized.

---

# 24. Error Codes

```text
ADMIN_REQUIRED
ADMIN_ACTION_NOT_ALLOWED
USER_NOT_FOUND
USER_ALREADY_SUSPENDED
USER_NOT_SUSPENDED
REPORT_NOT_FOUND
REPORT_ALREADY_RESOLVED
REPORT_ACTION_NOT_ALLOWED
ACCOUNT_DELETION_NOT_ALLOWED
```

---

# 25. Pagination

Admin lists must be paginated.

Examples:

```text
users
reports
audit logs
```

Offset pagination is acceptable initially.

---

# 26. Search and Filtering

Admin may need controlled filters.

Examples:

```text
status=ACTIVE
status=SUSPENDED
report_status=OPEN
username=...
```

Do not expose arbitrary SQL-like query parameters.

---

# 27. Security

Admin endpoints require:

```text
JWT authentication
ADMIN role
active admin account
action-level authorization
```

Consider stronger protection later:

```text
MFA
step-up authentication
restricted admin network
```

Not required initially unless product/security needs increase.

---

# 28. Rate Limiting

Admin actions should be protected against accidental/repeated execution.

Particularly destructive actions should be idempotent or state-aware.

Example:

```text
suspend already-suspended user
```

should not corrupt state.

---

# 29. Transaction Boundaries

Suspend:

```text
BEGIN
  update status
  revoke refresh sessions
COMMIT
```

Then:

```text
disconnect realtime sessions
cleanup Redis state
audit
```

Audit may be part of the same durable transaction where practical.

---

# 30. Admin UI Flow

```text
Admin Login
   ↓
Dashboard
   ├── Users
   └── Reports
```

User moderation:

```text
Users
 ↓
Open User
 ↓
View status/profile/moderation summary
 ↓
Suspend / Reactivate
```

Report moderation:

```text
Reports
 ↓
Open report
 ↓
Review approved context
 ↓
Resolve / Dismiss / Suspend user
```

---

# 31. Failure Handling

If status update fails:

```text
do not claim moderation action succeeded
```

If Redis disconnect cleanup fails after durable suspension:

```text
account status remains suspended
future authorization must reject user
retry/cleanup active realtime state
```

Durable account state is authoritative.

---

# 32. Testing

## Authorization

- normal user denied all admin endpoints
- unauthenticated denied
- active admin succeeds
- suspended admin denied

## User Moderation

- list users paginated
- suspend active user
- duplicate suspend handled
- refresh tokens revoked
- realtime session removed
- activate suspended user

## Reports

- list OPEN reports
- view report
- resolve
- dismiss
- invalid state transition denied

## Audit

- sensitive action creates audit record
- normal user cannot read audit records

## Privacy

- password/OTP/tokens never exposed
- message content not exposed unless explicit policy exists

---

# 33. Definition of Done — Admin

- [ ] ADMIN role is enforced server-side.
- [ ] Normal users cannot access Admin APIs.
- [ ] Admin user list is paginated.
- [ ] Admin can inspect approved user details.
- [ ] Admin can view reports.
- [ ] Admin can resolve/dismiss reports.
- [ ] Admin can suspend users.
- [ ] Suspension revokes sessions.
- [ ] Suspended user is removed from realtime activity.
- [ ] Admin can reactivate allowed users.
- [ ] Sensitive admin actions are audited.
- [ ] Admin does not bypass domain boundaries.
- [ ] Private auth secrets are never exposed.
- [ ] Destructive deletion waits for retention policy if unresolved.
- [ ] Automated authorization/moderation tests pass.

---

# 34. Open Decisions

1. Exact Admin MVP actions.
2. Admin ability to edit profile fields.
3. Admin access to message content.
4. Account deletion vs audit/report retention.
5. Audit retention period.
6. Whether MFA is required later.
7. Whether multiple admin permission levels are needed.
8. Last-admin/self-suspension policies.
9. Whether reports automatically enter UNDER_REVIEW when opened.
10. Whether users are notified of moderation action.

---

# 35. Workflow Diagram

```text
ADMIN LOGIN
    ↓
REQUIRE ADMIN ROLE
    ↓
ADMIN DASHBOARD
 ┌───────┴────────┐
 ▼                ▼
USERS           REPORTS
 │                │
 ▼                ▼
VIEW USER      OPEN REPORT
 │                │
 ├─ SUSPEND       ├─ RESOLVE
 ├─ ACTIVATE      ├─ DISMISS
 └─ DELETE*       └─ MODERATION ACTION
      │
      * only after
      deletion policy finalized

Every sensitive action
        ↓
     AUDIT LOG
```
