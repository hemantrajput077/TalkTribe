# TalkTribe — EPIC-02 Bug Fix Tickets

**Epic:** EPIC-02 — User Profile & Language Foundation  
**Milestone:** M2 — Profile + Language Foundation (stabilisation)  
**Source:** `docs/bugs.md`  
**Priority:** Fix Ticket 1 before any M3 work begins. Ticket 2 runs in parallel with early M3.

---

---

# Ticket 1 — PROF-BUG-01

## Title

**Fix critical M2 profile bugs blocking M3 (wrong query field, data loss on PATCH, missing validation, broken peer schema)**

## Issue Type

`Bug`

## Epic

`EPIC-02 — User Profile & Language Foundation`

## Bug IDs Covered

`BUG-01`, `BUG-03`, `BUG-04`, `BUG-05` — see `docs/bugs.md`

## Milestone

`M2 — Profile + Language Foundation (stabilisation)`

## Priority

`Critical`

## Environment

`backend/app/domains/profile/`

---

## Observed Behavior

Four separate defects exist in the Profile domain that break contracts already consumed or
about to be consumed by M3 Matching:

**BUG-01 — `GET /profiles/{user_id}` returns the wrong user's profile**

`ProfileRepository.get_safe_profile` filters by `Profile.id` (the internal auto-increment PK)
instead of `Profile.user_id`. A request for user 5 returns the profile whose
row-level `id` is 5, which is a different user. Silently returns wrong data.

**BUG-03 — `PATCH /profiles/me` clears fields not included in the request**

`ProfileRepository.update_profile` overwrites every field with the value from
`ProfileUpdate`, including fields that were not sent and therefore default to `None`.
A user who sends `{"location": "Mumbai"}` loses their existing bio and profession.

**BUG-04 — `ProfileUpdate` accepts oversized field values**

The `ProfileUpdate` Pydantic schema has no `max_length` constraints.
A client may submit a bio of unlimited length and receive HTTP 200.
The PROF-02 acceptance criterion "validation rejects oversized fields → 422" is not met.

**BUG-05 — `UserProfileResponse` inherits from the write schema and is missing `user_id`**

`UserProfileResponse` extends `ProfileUpdate` (an input schema) and exposes the
internal auto-increment `id` instead of the public `user_id`.
The roadmap M2 exit criterion "Matching-safe profile summary contract exists" requires
`user_id` to be present in the peer response. Matching cannot identify whose profile
it received.

---

## Expected Behavior

- `GET /profiles/{user_id}` returns the profile belonging to `user_id`, not to profile row `id`.
- `PATCH /profiles/me` with `{"location": "Mumbai"}` updates only `location`; bio and profession are unchanged.
- `PATCH /profiles/me` with a bio longer than 500 characters returns HTTP 422.
- `GET /profiles/{user_id}` response schema contains `user_id` and is defined independently of any write schema.

---

## Steps to Reproduce

**BUG-01:**
1. Create two users. User A has `user_id=1` (profile row `id=1`). User B has `user_id=2` (profile row `id=2`).
2. `GET /api/v1/profiles/2` returns User B's profile correctly at this point.
3. Delete User A's profile row. Now User B's profile row has `id=1`.
4. `GET /api/v1/profiles/2` returns 404 even though User B exists — because no row has `id=2`.

**BUG-03:**
1. Set bio to "Hello world" via `PATCH /profiles/me` with `{"bio": "Hello world"}`.
2. Verify bio is saved.
3. Send `PATCH /profiles/me` with `{"location": "Mumbai"}` only.
4. Fetch profile — bio is now `null`.

**BUG-04:**
1. Send `PATCH /profiles/me` with `{"bio": "<501-character string>"}`.
2. Observe HTTP 200 — should be HTTP 422.

**BUG-05:**
1. Call `GET /api/v1/profiles/{user_id}`.
2. Observe that the response contains `id` (internal PK) but no `user_id` field.
3. Observe that `user_id` cannot be derived from the response.

---

## Root Cause

| Bug | File | Line | Root cause |
|---|---|---|---|
| BUG-01 | `infrastructure/profile_repository.py` | 42 | `Profile.id` used instead of `Profile.user_id` in WHERE clause |
| BUG-03 | `infrastructure/profile_repository.py` | 29–35 | All fields assigned unconditionally, including `None` defaults |
| BUG-04 | `schemas/profile.py` | 20–24 | `ProfileUpdate` has no Pydantic `Field(max_length=...)` constraints |
| BUG-05 | `schemas/profile.py` | 27–30 | `UserProfileResponse` inherits `ProfileUpdate` and omits `user_id` |

---

## Fix Approach

**BUG-01** — `profile_repository.py:42`
```python
# Change
select(Profile).where(Profile.id == user_id)
# To
select(Profile).where(Profile.user_id == user_id)
```

**BUG-03** — `profile_repository.py:29`

Use `model_dump(exclude_unset=True)` to apply only fields explicitly sent by the client:
```python
update_data = profile_data.model_dump(exclude_unset=True)
for field, value in update_data.items():
    setattr(profile, field, value)
```

**BUG-04** — `schemas/profile.py`

Add `Field` constraints to `ProfileUpdate`:
```python
from pydantic import Field

class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bio:        str | None = Field(default=None, max_length=500)
    profession: str | None = Field(default=None, max_length=100)
    location:   str | None = Field(default=None, max_length=100)
```

**BUG-05** — `schemas/profile.py`

Replace the broken class with a standalone read schema:
```python
class PeerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id:    int
    bio:        str | None
    profession: str | None
    location:   str | None
    avatar_url: str | None
```

Update `routes.py` to use `PeerProfileResponse` on `GET /profiles/{user_id}`.

---

## In Scope

- Fix the `WHERE` clause in `get_safe_profile`
- Fix partial-update logic in `update_profile`
- Add `max_length` constraints to `ProfileUpdate`
- Replace `UserProfileResponse` with a properly defined `PeerProfileResponse` containing `user_id`
- Update the route that uses each corrected schema

## Out of Scope

- Account-status check on peer profile endpoint (covered by PROF-BUG-02)
- Custom interests (covered by PROF-BUG-02)
- Profile photo (PROF-07, blocked on storage decision)
- Any M3 feature work

---

## Dependencies

```
Blocked by: none — all changes are self-contained in Profile domain
Blocks: M3 Matching cannot begin until this is merged
Relates to: PROF-02, PROF-03
```

## Architecture References

- `docs/architecture/database.md` — Profile domain table ownership
- `docs/planning/epic-02-jira-stories.md` — PROF-02 and PROF-03 acceptance criteria
- `docs/bugs.md` — BUG-01, BUG-03, BUG-04, BUG-05

---

## Acceptance Criteria

**AC1 — Peer profile returns the correct user**

Given user A has `user_id=5`  
When `GET /api/v1/profiles/5` is called  
Then the response contains A's profile data, not any other user's.

**AC2 — Partial update preserves unset fields**

Given a user with `bio="Hello"` and `location=null`  
When `PATCH /api/v1/profiles/me` is called with `{"location": "Mumbai"}`  
Then `location` is updated to "Mumbai"  
And `bio` remains "Hello".

**AC3 — Oversized bio returns 422**

Given an authenticated user  
When `PATCH /api/v1/profiles/me` is called with a bio longer than 500 characters  
Then the API returns HTTP 422.

**AC4 — Oversized profession returns 422**

Given an authenticated user  
When `PATCH /api/v1/profiles/me` is called with a profession longer than 100 characters  
Then the API returns HTTP 422.

**AC5 — Peer profile response contains `user_id`**

Given any call to `GET /api/v1/profiles/{user_id}`  
Then the response body contains `user_id` equal to the requested user's ID.  
And the response does not expose the internal auto-increment profile `id`.

**AC6 — Peer profile response never inherits write schema fields**

Given any peer profile response  
Then the response schema does not contain write-only or input-only fields.

---

## API Impact

```
PATCH /api/v1/profiles/me
  — Request: same endpoint, now validates max_length
  — Response: unchanged schema (ProfileResponse)
  — Behaviour change: partial update now truly partial

GET /api/v1/profiles/{user_id}
  — Response schema changes: id removed, user_id added
  — Breaking change for any existing caller (Matching will consume the fixed schema)
```

## Database Impact

None. No new tables or migrations required. All fixes are application-layer only.

## Security / Authorization

- No authorization changes.
- `extra="forbid"` added to `ProfileUpdate` prevents unknown field injection.

---

## Test Requirements

- `GET /profiles/{user_id}` returns correct user when profile row `id ≠ user_id`
- `PATCH /profiles/me` with one field does not clear other existing fields
- `PATCH /profiles/me` with bio > 500 chars returns 422
- `PATCH /profiles/me` with profession > 100 chars returns 422
- `GET /profiles/{user_id}` response contains `user_id`, not internal `id`
- Existing profile tests continue to pass

---

## Definition of Done

- [ ] BUG-01 fix merged — `get_safe_profile` queries by `Profile.user_id`
- [ ] BUG-03 fix merged — `update_profile` uses `exclude_unset=True`
- [ ] BUG-04 fix merged — `ProfileUpdate` has `max_length` constraints
- [ ] BUG-05 fix merged — `PeerProfileResponse` is standalone with `user_id`
- [ ] All new acceptance criteria have passing tests
- [ ] Existing profile test suite still passes
- [ ] Ruff + mypy pass
- [ ] `docs/bugs.md` updated — BUG-01, 03, 04, 05 marked resolved
- [ ] PR merged before any M3 branch is created

---

---

# Ticket 2 — PROF-BUG-02

## Title

**Fix peer profile account-status check and implement custom interests (parallel M3 track)**

## Issue Type

`Bug + Story` (two independent items grouped as one parallel-track ticket; split into separate PRs)

## Epic

`EPIC-02 — User Profile & Language Foundation`

## Bug / Story IDs Covered

`BUG-02` (bug) + `BUG-06` / `PROF-04 custom interests` (story)

## Milestone

`M2 — Profile + Language Foundation (stabilisation)`

## Priority

`High`

## Constraint

Must both be merged before M3 Matching or Pairing features ship.  
Neither blocks M3 from *starting*. Both block M3 from *completing*.

---

---

## Part A — BUG-02: Peer profile does not check account status

### Issue Type

`Bug`

### Observed Behavior

`GET /api/v1/profiles/{user_id}` returns HTTP 200 with a profile even when the account
whose `user_id` was requested has `account_status = SUSPENDED`, `BLOCKED`, or `DELETED`.
Only the `profiles` table is queried — the `users` table is never joined to verify account status.

### Expected Behavior

`GET /api/v1/profiles/{user_id}` returns HTTP 404 for any user whose `account_status`
is not `ACTIVE`. The response must not reveal the reason (do not return 403 with
"account suspended" — return 404 so callers cannot enumerate account states).

### Root Cause

`ProfileRepository.get_safe_profile` queries only the `profiles` table.
`ProfileService.get_safe_profile` never receives account status from the `users` table.

**File:** `backend/app/domains/profile/infrastructure/profile_repository.py:42`  
**File:** `backend/app/domains/profile/application/profile_service.py:57`

### Fix Approach

The Profile domain must not import from the Auth repository directly (domain boundary rule).
The correct approach is a JOIN within the profile query:

```python
from app.domains.auth.infrastructure.user_model import User
from app.domains.auth.domain.enums import AccountStatus

async def get_safe_profile(self, user_id: int) -> Profile | None:
    result = await self.db.execute(
        select(Profile)
        .join(User, User.id == Profile.user_id)
        .where(
            Profile.user_id == user_id,
            User.account_status == AccountStatus.ACTIVE,
        )
    )
    return result.scalar_one_or_none()
```

This is a read-only join for status filtering — it does not violate domain ownership because
Profile does not write to or depend on Auth business logic, only reads the status value.

### Acceptance Criteria

**AC1 — Active account profile is returned**

Given a user with `account_status = ACTIVE`  
When `GET /api/v1/profiles/{user_id}` is called  
Then the API returns HTTP 200 with the profile.

**AC2 — Suspended account returns 404**

Given a user with `account_status = SUSPENDED`  
When `GET /api/v1/profiles/{user_id}` is called  
Then the API returns HTTP 404.

**AC3 — Deleted account returns 404**

Given a user with `account_status = DELETED`  
When `GET /api/v1/profiles/{user_id}` is called  
Then the API returns HTTP 404.

**AC4 — Response never reveals account status**

Given any inactive account  
When the endpoint returns 404  
Then the response body does not contain words like "suspended", "blocked", or "deleted".

### API Impact

```
GET /api/v1/profiles/{user_id}
  — No schema change
  — Behaviour change: inactive accounts now return 404 instead of 200
```

### Database Impact

None. No new tables or migrations. Read-only JOIN on existing tables.

### Test Requirements

- ACTIVE user returns 200
- SUSPENDED user returns 404
- DELETED user returns 404
- BLOCKED user returns 404
- Response body for 404 does not expose account_status value

---

---

## Part B — PROF-04 (custom interests): Learner can submit custom interest names

### Issue Type

`Story`

### Feature ID

`PROF-04 (custom interests slice)`

### User Story

As a learner,  
I want to add an interest that is not in the predefined list,  
so that I can accurately describe my interests for better matching.

### Business Context

The M2 roadmap exit criterion states "Custom interests work". The predefined
interest catalogue covers common topics, but users with niche hobbies cannot
represent themselves accurately using only the predefined list. This is an M2
closure requirement — Matching in M3 already reads `user_interests` and will
benefit from richer interest data immediately.

### In Scope

- User may submit a free-text string as a custom interest name via the existing
  `PUT /api/v1/profiles/me/interests` endpoint (no new endpoint needed)
- Custom interest names are trimmed, lowercased for deduplication, then stored
  with display-friendly casing
- Rejected if: empty after trim, longer than 50 characters, or an exact
  normalised match to an already-existing interest (predefined or custom)
- Custom interests are stored in the shared `interests` table with `is_predefined=False`
  and `created_by_user_id` set to the submitting user
- `GET /api/v1/interests` returns only predefined interests (`is_predefined=True`)
- The 10-interest maximum applies across both predefined and custom interests combined
- Schema migration required to add `is_predefined`, `created_by_user_id`, `is_active`, `created_at`
  columns to the `interests` table

### Out of Scope

- Admin moderation or approval queue for custom interests (future)
- Deduplication across near-similar strings, e.g. "guitar" vs "guitars" (future)
- Exposing custom interests in a separate catalogue endpoint (future)
- Custom interest deletion by the user (future)

### Request Schema Change

Extend `PUT /api/v1/profiles/me/interests` to accept an optional list of custom strings
alongside existing predefined IDs:

```json
{
  "interest_ids": [1, 3, 7],
  "custom_interests": ["Origami", "Urban Sketching"]
}
```

The combined count of `interest_ids` + `custom_interests` must not exceed 10.

### Database Impact

```sql
-- Migration required: extend interests table
ALTER TABLE interests
  ADD COLUMN is_predefined       BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN created_by_user_id  INTEGER REFERENCES users(id) ON DELETE SET NULL,
  ADD COLUMN is_active           BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN created_at          TIMESTAMPTZ NOT NULL DEFAULT now();

-- Backfill existing rows (all seeded rows are predefined)
UPDATE interests SET is_predefined = TRUE WHERE is_predefined IS NULL;
```

### Architecture References

- `docs/architecture/database.md` — Section 8.1 `interests` table definition
- `docs/workflows/profile.md` — Sections 17–20 Interest Selection and Normalization
- `docs/planning/epic-02-jira-stories.md` — PROF-04 In Scope

### Acceptance Criteria

**AC1 — Custom interest is saved and returned**

Given an authenticated user  
When they call `PUT /api/v1/profiles/me/interests` with `{"interest_ids": [1], "custom_interests": ["Origami"]}`  
Then "Origami" is stored as a new interest with `is_predefined=False`  
And the response includes "Origami" in the selected interests list.

**AC2 — Custom interest is deduplicated against existing interests**

Given "Origami" already exists in the interests table (from any user)  
When another user submits `"custom_interests": ["origami"]`  
Then no duplicate row is created  
And the existing "Origami" interest is linked to the user.

**AC3 — Empty or whitespace-only custom interest is rejected**

Given a custom interest string of `"   "`  
When submitted  
Then the API returns HTTP 422.

**AC4 — Custom interest longer than 50 characters is rejected**

Given a custom interest name longer than 50 characters  
When submitted  
Then the API returns HTTP 422.

**AC5 — Combined total exceeds 10 returns 422**

Given `interest_ids` has 8 entries and `custom_interests` has 3 entries  
When submitted  
Then the API returns HTTP 422.

**AC6 — `GET /api/v1/interests` returns only predefined interests**

Given custom interests exist in the database  
When `GET /api/v1/interests` is called  
Then only interests with `is_predefined=True` are returned.

**AC7 — PUT replaces all previous selections including custom**

Given a user with existing predefined and custom interest selections  
When they call `PUT /api/v1/profiles/me/interests` with a new list  
Then all previous selections are removed  
And only the new selections are saved.

### Security / Authorization

- Authenticated owner only for `PUT /api/v1/profiles/me/interests`
- Custom interest text is trimmed and validated server-side — client cannot inject arbitrary-length strings
- `created_by_user_id` is set from the authenticated identity, never from the request body

### Test Requirements

- Valid custom interest is saved with `is_predefined=False`
- Duplicate custom interest (case-insensitive) reuses existing row
- Empty/whitespace custom interest returns 422
- Name > 50 chars returns 422
- Combined count > 10 returns 422
- `GET /interests` does not include custom interests
- PUT replaces custom interests along with predefined ones
- Unauthenticated update returns 401

### Definition of Done — Part B

- [ ] `interests` table migration adds `is_predefined`, `created_by_user_id`, `is_active`, `created_at`
- [ ] Existing seeded rows backfilled with `is_predefined=TRUE`
- [ ] `UpdateInterestsRequest` schema extended with `custom_interests` field
- [ ] `InterestService` handles normalisation, deduplication, and persistence of custom interests
- [ ] `GET /api/v1/interests` filters to `is_predefined=TRUE` only
- [ ] All acceptance criteria have passing tests
- [ ] Ruff + mypy pass
- [ ] `docs/bugs.md` updated — BUG-06 marked resolved

---

## Combined Definition of Done — Ticket 2

- [ ] Part A (BUG-02) merged — peer profile endpoint checks account_status
- [ ] Part B (custom interests) merged — custom interest submission works end-to-end
- [ ] `docs/bugs.md` updated — BUG-02 and BUG-06 marked resolved
- [ ] Both PRs merged before M3 Matching or Pairing is marked complete
