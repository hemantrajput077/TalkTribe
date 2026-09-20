# TalkTribe — Known Bugs

**Scope:** M2 Profile + Language Foundation  
**Last updated:** 2026-09-16  
**Status:** Open

---

## BUG-01 — `GET /profiles/{user_id}` queries the wrong database field

**Severity:** Critical  
**Story:** PROF-03  
**File:** `backend/app/domains/profile/infrastructure/profile_repository.py:42`

### What is wrong

`get_safe_profile` filters by `Profile.id` (the auto-increment primary key) instead of `Profile.user_id`.

```python
# Current — WRONG
result = await self.db.execute(select(Profile).where(Profile.id == user_id))

# Should be
result = await self.db.execute(select(Profile).where(Profile.user_id == user_id))
```

### Impact

`GET /api/v1/profiles/3` returns the profile whose internal auto-increment `id` is 3, not the profile belonging to user 3. Because `user_id` and the profile's own `id` are different sequences, this silently returns the wrong user's profile to the caller.

### Acceptance Criteria Broken

PROF-03 AC1 — "Authenticated user can view an active peer's profile" is not met correctly.

---

## BUG-02 — Peer profile endpoint does not check account status

**Severity:** High  
**Story:** PROF-03  
**File:** `backend/app/domains/profile/infrastructure/profile_repository.py:42`  
**File:** `backend/app/domains/profile/application/profile_service.py:57`

### What is wrong

`get_safe_profile` queries only the `profiles` table. It never checks `users.account_status`. A suspended, blocked, or deleted user's profile is returned as HTTP 200 instead of HTTP 404.

### Impact

PROF-03 requires that inactive accounts (SUSPENDED, BLOCKED, DELETED) return 404. A caller — including Matching — cannot trust that a profile returned from this endpoint belongs to an active user.

### Acceptance Criteria Broken

PROF-03 AC2 — "Non-existent or inactive user returns 404" is not enforced.

---

## BUG-03 — `PATCH /profiles/me` overwrites all fields instead of doing a partial update

**Severity:** High  
**Story:** PROF-02  
**File:** `backend/app/domains/profile/infrastructure/profile_repository.py:29`

### What is wrong

`update_profile` unconditionally assigns every field from `ProfileUpdate`, including fields that default to `None` when not sent in the request body.

```python
# Current — WRONG
profile.bio        = profile_data.bio        # becomes None if not sent
profile.profession = profile_data.profession # becomes None if not sent
profile.location   = profile_data.location   # becomes None if not sent
```

### Impact

A user who sends `PATCH /profiles/me` with only `{"location": "Mumbai"}` will have their existing `bio` and `profession` silently cleared. This is a data-loss bug.

### Fix direction

Only update fields that were explicitly provided in the request. Use `model_fields_set` from Pydantic to detect which fields were actually sent:

```python
update_data = profile_data.model_dump(exclude_unset=True)
for field, value in update_data.items():
    setattr(profile, field, value)
```

### Acceptance Criteria Broken

PROF-02 AC2 — "Partial update only changes sent fields" is not met.

---

## BUG-04 — `ProfileUpdate` schema has no field-length validators

**Severity:** Medium  
**Story:** PROF-02  
**File:** `backend/app/domains/profile/schemas/profile.py`

### What is wrong

`ProfileUpdate` defines no maximum-length constraints on its fields. The PROF-02 ticket specifies:

- `bio` — max 500 characters  
- `profession` — max 100 characters  
- `location` — max 100 characters

```python
# Current — no validators
class ProfileUpdate(BaseModel):
    bio: str | None = None
    profession: str | None = None
    location: str | None = None
    avatar_url: str | None = None
```

### Impact

A user can submit an arbitrarily long bio or profession. FastAPI returns HTTP 200 and the oversized value is written to the database, limited only by the underlying PostgreSQL column type.

### Fix direction

Add `Field` constraints:

```python
from pydantic import Field

class ProfileUpdate(BaseModel):
    bio: str | None = Field(default=None, max_length=500)
    profession: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=100)
```

### Acceptance Criteria Broken

PROF-02 AC3 — "Validation rejects oversized fields" returns HTTP 422 is not met.

---

## BUG-05 — `UserProfileResponse` schema is misdesigned and missing `user_id`

**Severity:** Medium  
**Story:** PROF-03  
**File:** `backend/app/domains/profile/schemas/profile.py:27`

### What is wrong

`UserProfileResponse` inherits from `ProfileUpdate` — an *input/write* schema — and adds only an `id` field (the auto-increment primary key). It is missing `user_id`, which every downstream consumer (Matching, Pairing, Friendship, Calls) needs to identify whose profile they received.

```python
# Current — wrong base class, missing user_id
class UserProfileResponse(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: int
```

### Impact

- Callers receive `id` (internal PK) but not `user_id` (the public identity).  
- The roadmap M2 exit criterion "Matching-safe profile summary contract exists" requires `user_id` to be present.  
- Using a write schema as a response schema base is a design violation that will cause confusion as both schemas evolve independently.

### Fix direction

Define `UserProfileResponse` (or `PeerProfileResponse`) as a standalone read schema:

```python
class PeerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    bio: str | None
    profession: str | None
    location: str | None
    avatar_url: str | None
```

### Acceptance Criteria Broken

PROF-03 AC3 — "Auth/private fields are never in the response" is partially met, but the contract is incomplete because `user_id` is absent.

---

## BUG-06 — Custom interests not implemented (M2 exit criterion unmet)

**Severity:** Medium  
**Story:** PROF-04  
**File:** `backend/app/domains/profile/infrastructure/interest_model.py`  
**File:** `backend/app/domains/profile/application/interest_service.py`

### What is wrong

The roadmap M2 exit criterion states: **"Custom interests work"**. Neither the `Interest` model nor `InterestService` supports submitting a free-text custom interest. The service only validates IDs against the predefined catalogue and rejects anything not already there.

The `interests` table is also missing columns the database architecture design requires for custom-interest support:

| Required column | Present |
|---|---|
| `is_predefined` | No |
| `created_by_user_id` | No |
| `is_active` | No |
| `created_at` | No |

### Impact

Users cannot add interests that are not in the predefined seed list. The M2 milestone cannot be closed until this is implemented.

### Note

This is both a missing feature and a schema gap. The `interests` model migration will need to be extended before custom interest logic can be added.

---

## Schema Gaps (Database Design vs. Implementation)

These are columns specified in `docs/architecture/database.md` that are absent from the current models. They do not cause immediate runtime failures but leave the schema incomplete against the architecture baseline.

| Model | File | Missing columns |
|---|---|---|
| `Language` | `domains/languages/infrastructure/language_model.py` | `is_active`, `created_at` |
| `UserLanguage` | `domains/profile/infrastructure/user_language_model.py` | `is_primary`, `created_at`, `updated_at` |
| `Interest` | `domains/profile/infrastructure/interest_model.py` | `is_predefined`, `created_by_user_id`, `is_active`, `created_at` |

The `Interest` gaps are directly linked to BUG-06 (custom interests). The `Language` and `UserLanguage` gaps are lower priority and do not break any current feature.

---

## M2 Exit Criteria — Bug Impact Summary

| Criterion | Status |
|---|---|
| User can retrieve own profile | Done |
| User can update own profile | **Broken** — BUG-03, BUG-04 |
| Authenticated users can view peer profile | **Broken** — BUG-01, BUG-02 |
| Private auth fields never exposed | Done |
| Interests work (predefined) | Done |
| Custom interests work | **Missing** — BUG-06 |
| English exists as supported language | Done |
| A1–C2 proficiency works | Done |
| Profile completeness can be evaluated | Done |
| Matching-safe profile summary contract | **Incomplete** — BUG-05 |
| Pairing can check profile eligibility | Done |
