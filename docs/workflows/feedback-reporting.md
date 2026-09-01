# TalkTribe Feedback and Reporting Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** Feedback / Reporting / Moderation Input  
**Depends on:** `VOICE_CALL_WORKFLOW.md`, `PROFILE_WORKFLOW.md`, `FRIENDSHIP_WORKFLOW.md`, `ADMIN_WORKFLOW.md`, `SECURITY_ARCHITECTURE.md`

---

# 1. Purpose

This document defines the post-interaction feedback and user-reporting workflow.

It covers:

- post-call rating
- rating eligibility
- rating aggregation
- reporting another user
- report linkage to calls/conversations
- blocking after report
- admin review handoff
- privacy
- abuse prevention
- testing
- Definition of Done

---

# 2. Product Goal

After talking with a co-learner, the user should be able to:

```text
rate learner
report learner
connect to another learner
```

Feedback supports trust and future matching/profile signals.

Reporting supports safety and Admin moderation.

---

# 3. Post-Call Prompt

After an eligible completed call:

```text
call.ended
   ↓
frontend shows:
Rate this learner
Report this learner
Find another learner
```

Rating/reporting should not block the user from leaving the flow.

---

# 4. Rating Eligibility

A user may rate only when:

```text
authenticated
was a participant in call
rating target was the other participant
call reached an eligible state
rating not already submitted by reviewer for that call
```

Recommended eligible call state:

```text
ENDED after actual connection
```

Do not allow arbitrary rating of users with whom no call occurred.

---

# 5. Rating Data

Recommended:

```text
call_id
reviewer_user_id
reviewed_user_id
rating
feedback_text optional
created_at
```

Recommended rating scale:

```text
1–5
```

This should be finalized before implementation.

---

# 6. Submit Rating

```text
POST /api/v1/calls/{call_id}/feedback
        ↓
authenticate reviewer
        ↓
load call
        ↓
verify reviewer participated
        ↓
verify call eligible
        ↓
verify target is other participant
        ↓
verify no existing review from same reviewer/call
        ↓
validate rating
        ↓
persist
        ↓
return success
```

---

# 7. Duplicate Rating

Recommended:

```text
one rating per reviewer per call
```

If already submitted:

```text
FEEDBACK_ALREADY_SUBMITTED
```

Whether users may edit a rating later is open.

---

# 8. Rating Aggregation

Profile rating should preferably be derived from feedback records.

Conceptually:

```text
average_rating
rating_count
```

Do not blindly maintain duplicated counters unless performance needs justify it.

---

# 9. Rating Visibility

Possible authenticated profile display:

```text
4.6
27 ratings
```

Individual reviewer identity or raw feedback should not automatically be public.

Exact feedback visibility is a product decision.

---

# 10. Reporting Eligibility

A user should be able to report another user when there is a legitimate interaction context.

Possible contexts:

```text
after a voice call
from a conversation
from a user profile
```

For MVP, call/report context is especially important.

---

# 11. Report Data

Recommended:

```text
reporter_user_id
reported_user_id
call_id optional
conversation_id optional
reason
details optional
status
created_at
resolved_at
resolved_by_admin_id
```

Statuses:

```text
OPEN
UNDER_REVIEW
RESOLVED
DISMISSED
```

---

# 12. Report Reasons

Use controlled categories where possible.

Examples:

```text
HARASSMENT
ABUSIVE_LANGUAGE
SPAM
INAPPROPRIATE_BEHAVIOR
IMPERSONATION
OTHER
```

Exact list should be approved before implementation.

---

# 13. Submit Report

```text
User selects Report
        ↓
choose reason
        ↓
optional details
        ↓
POST /api/v1/reports
        ↓
authenticate
        ↓
validate reporter != reported
        ↓
validate target exists
        ↓
validate referenced call/conversation if supplied
        ↓
persist OPEN report
        ↓
return confirmation
        ↓
Admin workflow can review
```

---

# 14. Report + Block

After submitting a report, frontend may offer:

```text
Block this user
```

Reporting and blocking are separate actions.

A report should not silently create a block unless product explicitly decides that behavior.

---

# 15. Blocking After Report

If user blocks:

```text
Friendship/Blocking workflow
```

then:

```text
future matching denied
messages denied
calls denied
friend requests denied
```

---

# 16. False / Duplicate Reports

MVP should prevent obvious duplicate spam.

Possible rule:

```text
same reporter
same target
same call/context
same unresolved report
```

→ avoid duplicate creation.

Do not prevent legitimate new reports for separate incidents.

---

# 17. Abuse Prevention

Protect report submission with:

```text
authentication
rate limiting
payload length limits
controlled reason values
```

Future systems may detect abusive reporting patterns.

---

# 18. Admin Handoff

New report:

```text
status = OPEN
```

Admin can:

```text
view
review context
change status
resolve
dismiss
take user moderation action
```

Report handling details belong to Admin workflow.

---

# 19. Privacy

Normal users should not see:

```text
who else reported a user
admin notes
internal moderation status beyond their own submission if not needed
```

Admins may access moderation context according to policy.

---

# 20. Message/Call Evidence

Whether Admin may inspect message content or detailed call metadata for moderation remains open.

Voice media is not stored.

Therefore reports about calls rely on:

```text
participants
timestamps
call metadata
user-provided report details
```

unless future recording/moderation systems are explicitly introduced.

---

# 21. Rating and Matching

Future matching may use rating as a signal.

MVP matching should not automatically depend heavily on rating unless explicitly approved.

Keep rating available through a contract.

---

# 22. Rating and Profile

Profile may show:

```text
average rating
rating count
```

Only if product design enables it.

---

# 23. API Surface

Recommended:

```text
POST /api/v1/calls/{call_id}/feedback
POST /api/v1/reports
```

Possible:

```text
GET /api/v1/profiles/{user_id}/rating
GET /api/v1/reports/me
```

Only if product requires them.

---

# 24. Error Codes

```text
FEEDBACK_NOT_ALLOWED
FEEDBACK_ALREADY_SUBMITTED
INVALID_RATING
CALL_NOT_ELIGIBLE_FOR_FEEDBACK
REPORT_NOT_ALLOWED
REPORT_ALREADY_EXISTS
INVALID_REPORT_REASON
REPORT_TARGET_INVALID
```

---

# 25. Transactions

Feedback:

```text
BEGIN
  validate uniqueness
  insert feedback
COMMIT
```

Report:

```text
BEGIN
  validate context
  insert report
COMMIT
```

Admin moderation action is separate.

---

# 26. Failure Handling

If feedback save fails:

```text
do not update/display rating as accepted
```

If report save fails:

```text
show failure
allow retry
```

Never claim a safety report was recorded when persistence failed.

---

# 27. Testing

## Feedback

- call participant can rate
- non-participant denied
- target must be other participant
- invalid rating denied
- duplicate rating denied
- aggregate rating correct

## Reporting

- valid report succeeds
- self report denied
- invalid target denied
- referenced call membership validated
- duplicate context report handled
- rate limit works
- report reaches OPEN status

## Integration

- report appears in Admin review
- optional block remains separate
- profile rating excludes invalid/unapproved data as designed

---

# 28. Definition of Done — Feedback / Reporting

- [ ] Completed call can trigger feedback UI.
- [ ] Only eligible call participants can rate.
- [ ] Rating range is validated.
- [ ] Duplicate feedback per reviewer/call is prevented.
- [ ] Rating aggregation works.
- [ ] User can report another user.
- [ ] Report reason is validated.
- [ ] Report context can reference call/conversation.
- [ ] Reports are stored durably.
- [ ] New reports enter Admin moderation flow.
- [ ] Reporting does not silently block unless explicitly chosen.
- [ ] Rate limiting protects report abuse.
- [ ] Privacy rules are respected.
- [ ] Automated tests pass.

---

# 29. Open Decisions

1. Final rating scale.
2. Whether text feedback is MVP.
3. Whether ratings can be edited.
4. Whether raw text reviews are visible.
5. Exact report reason list.
6. Whether user sees own report status.
7. Duplicate report rule.
8. Whether Admin can access message content.
9. Whether rating influences matching in MVP.
10. Minimum call duration for rating eligibility.

---

# 30. Workflow Diagram

```text
CALL ENDS
   ↓
POST-CALL SCREEN
   ├───────────────┬────────────────┐
   ▼               ▼                ▼
 RATE            REPORT         FIND ANOTHER
   │               │
VALIDATE        SELECT REASON
PARTICIPANT        │
   │               ▼
SAVE FEEDBACK   SAVE OPEN REPORT
   │               │
   ▼               ▼
PROFILE RATING   ADMIN REVIEW
                   │
                   ▼
              MODERATION ACTION
```
