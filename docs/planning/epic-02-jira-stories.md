# TalkTribe — EPIC-02 Jira Stories

**Epic:** EPIC-02 — User Profile & Language Foundation
**Milestone:** M2 — Profile + Language Foundation
**Scope:** MVP
**Priority:** High
**Status:** Ready for implementation

**Primary references:**
- `DEVELOPMENT_ROADMAP.md` — M2 definition and slice order
- `DATABASE_ARCHITECTURE.md` — profiles, languages, interests table design
- `DOMAIN_BOUNDARIES.md` — Profile domain ownership rules
- `COMPONENT_ARCHITECTURE.md` — modular monolith structure
- `JIRA_GENERATION_RULES.md` — ticket format and rules

**Blocked by:**
- M1 Auth Stabilization (AuthenticatedIdentity contract — already delivered)

---

## Epic Summary

M2 creates the learner identity used by every later milestone.

Matching needs profile + language data to compute compatibility scores.
Pairing needs profile eligibility before queuing a user.
Calls need a safe profile summary for the peer display.

Without M2, none of M3–M8 can function correctly.

---

## M2 Story Index

| Story ID | Title | Priority | Blocked by |
|---|---|---|---|
| PROF-01 | Learner can view their own profile | High | AUTH-09 |
| PROF-02 | Learner can create and update their own profile | High | PROF-01 |
| PROF-03 | Authenticated user can view a peer's safe profile | High | PROF-01 |
| PROF-04 | Learner can add and manage interests | High | PROF-02 |
| PROF-05 | Learner can configure native and learning languages | Critical | PROF-02 |
| PROF-06 | System can evaluate whether a profile is complete | Critical | PROF-02, PROF-05 |
| PROF-07 | Learner can upload a profile photo | Medium | PROF-02 |

---

---

# Story 1 — PROF-01

## Title

**Learner can view their own profile**

## Epic

`EPIC-02 — User Profile & Language Foundation`

## Feature ID

`PROF-01`

## Milestone

`M2 — Profile + Language Foundation`

## Priority

High

## User Story

As a learner,
I want to retrieve my own profile,
so that I can see what information is currently saved and know what to complete.

## Business Context

This is the read foundation for the entire profile domain. Before a user can update
anything, the system must be able to return their own profile. It also unblocks
`PROF-02` (update), `PROF-03` (peer view), and the profile-completion check.

A profile record must be created automatically when a user completes registration,
or created lazily on first retrieval. The profile is permanently linked to the
authenticated user — a user can never retrieve someone else's full self-profile
through this endpoint.

## In Scope

- `profiles` database table and Alembic migration
- Auto-create a profile row linked to `users.id` on first retrieval if one does not exist
- `GET /api/v1/profiles/me` — returns the authenticated user's full own profile
- Response includes: `user_id`, `bio`, `profession`, `location`, `avatar_url`, `created_at`, `updated_at`
- Authorization: requires valid authenticated identity (`get_current_identity`)
- Domain follows modular monolith structure under `app/domains/profile/`

## Out of Scope

- Profile update (PROF-02)
- Peer profile view (PROF-03)
- Interests (PROF-04)
- Languages (PROF-05)
- Profile photo upload (PROF-07)
- Returning suspended/blocked account profiles

## Dependencies

```
Blocked by:
  AUTH-09 — AuthenticatedIdentity contract (DELIVERED)

Relates to:
  PROF-02 — Profile update (unblocked by this story)
  PROF-03 — Peer view (unblocked by this story)
```

## Architecture References

- `DATABASE_ARCHITECTURE.md` — profiles table definition
- `DOMAIN_BOUNDARIES.md` — Profile domain must not query Auth repositories directly
- `COMPONENT_ARCHITECTURE.md` — modular domain folder structure

## Acceptance Criteria

**AC1 — Authenticated retrieval returns own profile**

Given an authenticated learner with a valid access token
When they call `GET /api/v1/profiles/me`
Then the API returns HTTP 200
And the response contains the user's profile fields.

**AC2 — Unauthenticated request is rejected**

Given a request with no access token
When they call `GET /api/v1/profiles/me`
Then the API returns HTTP 401.

**AC3 — Profile created automatically on first retrieval**

Given a newly registered and verified user with no profile row
When they call `GET /api/v1/profiles/me`
Then a profile record is created with null/empty optional fields
And HTTP 200 is returned with the empty profile.

**AC4 — Sensitive auth fields never exposed**

Given any authenticated user
When they call `GET /api/v1/profiles/me`
Then the response never contains: `password_hash`, `role`, `account_status`, OTP data,
refresh-token data, or any field owned by the Auth domain.

**AC5 — Suspended/deleted accounts are rejected**

Given a user whose account_status is SUSPENDED, BLOCKED, or DELETED
When they call `GET /api/v1/profiles/me`
Then the API returns HTTP 403 (handled by the existing identity guard).

## Technical Notes

- The `profiles` table must have a `user_id` FK referencing `users.id` with `ON DELETE CASCADE`.
- Profile domain reads `user_id` from `AuthenticatedIdentity` — it must NOT join directly into the `users` table for auth fields.
- Repository pattern: `ProfileRepository(db)` with `get_by_user_id` and `create` methods.
- Application service: `ProfileService` wraps repository and owns lazy-creation logic.

## API Impact

```
GET /api/v1/profiles/me
Authorization: Bearer <access_token>

Response 200:
{
  "user_id": 1,
  "bio": null,
  "profession": null,
  "location": null,
  "avatar_url": null,
  "created_at": "...",
  "updated_at": "..."
}

Response 401: unauthenticated
Response 403: account not in good standing
```

## Database Impact

```sql
CREATE TABLE profiles (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    bio         TEXT,
    profession  VARCHAR(100),
    location    VARCHAR(100),
    avatar_url  VARCHAR(500),
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_profiles_user_id ON profiles(user_id);
```

New Alembic migration required.

## Security / Authorization

- Requires `get_current_identity` — JWT must be valid and not blocklisted.
- Account status guard already enforced by the identity dependency.
- Profile domain never exposes auth-owned fields.

## Test Requirements

- Authenticated user receives 200 with own profile data
- Unauthenticated request receives 401
- First retrieval auto-creates profile row and returns 200
- Response schema never contains password, role, OTP, or token fields
- Suspended user receives 403

## Definition of Done

- [ ] `profiles` migration created and applies cleanly
- [ ] `GET /api/v1/profiles/me` returns 200 for authenticated user
- [ ] Auto-creation on first call works
- [ ] Auth fields never appear in response
- [ ] All acceptance criteria have passing tests
- [ ] Ruff + mypy pass
- [ ] PR merged to main

---

---

# Story 2 — PROF-02

## Title

**Learner can create and update their own profile**

## Epic

`EPIC-02 — User Profile & Language Foundation`

## Feature ID

`PROF-02`

## Milestone

`M2 — Profile + Language Foundation`

## Priority

High

## User Story

As a learner,
I want to update my bio, profession, and location,
so that other users and the matching system can learn who I am.

## Business Context

A complete profile is required before a user can enter matching or pairing.
Profile update is how a user works toward profile completion.
The matching score will use profession and location as secondary signals.

## In Scope

- `PATCH /api/v1/profiles/me` — partial update of own profile
- Updatable fields: `bio`, `profession`, `location`
- Field validation: `bio` max 500 chars, `profession` max 100 chars, `location` max 100 chars
- Returns the updated full self-profile on success
- Only the authenticated owner can update their own profile
- Partial updates — any combination of the three fields may be sent

## Out of Scope

- Profile photo upload (PROF-07)
- Language update (PROF-05)
- Interests update (PROF-04)
- Updating another user's profile
- Changing `user_id`, `created_at`, or `updated_at` directly

## Dependencies

```
Blocked by:
  PROF-01 — profiles table and GET /profiles/me must exist

Relates to:
  PROF-04 — Interests (unblocked by this story)
  PROF-05 — Languages (unblocked by this story)
  PROF-06 — Eligibility check (depends on profile fields being settable)
```

## Architecture References

- `DATABASE_ARCHITECTURE.md` — profiles table
- `DOMAIN_BOUNDARIES.md` — Profile domain owns update rules

## Acceptance Criteria

**AC1 — Owner can update their profile**

Given an authenticated learner
When they send `PATCH /api/v1/profiles/me` with `{"bio": "I love learning English"}`
Then the bio is saved
And the API returns HTTP 200 with the updated profile.

**AC2 — Partial update works**

Given an authenticated learner with an existing bio
When they send `PATCH /api/v1/profiles/me` with only `{"location": "Mumbai"}`
Then only `location` is changed
And `bio` retains its previous value.

**AC3 — Validation rejects oversized fields**

Given an authenticated learner
When they send a `bio` longer than 500 characters
Then the API returns HTTP 422.

**AC4 — Unauthenticated request is rejected**

Given no access token
When `PATCH /api/v1/profiles/me` is called
Then the API returns HTTP 401.

**AC5 — Updated timestamp is refreshed**

Given an authenticated learner updates their profile
When the response is returned
Then `updated_at` reflects the time of the update.

## Technical Notes

- Use Pydantic model with `Optional` fields and `model_config = ConfigDict(extra="forbid")`.
- Repository `update_profile(user_id, **fields)` — only updates non-None fields.
- `updated_at` should be set in the repository or via a DB trigger/column default.

## API Impact

```
PATCH /api/v1/profiles/me
Authorization: Bearer <access_token>
Content-Type: application/json

Request (all fields optional):
{
  "bio": "I love learning English",
  "profession": "Software Engineer",
  "location": "Mumbai"
}

Response 200: updated profile object (same schema as GET /profiles/me)
Response 401: unauthenticated
Response 422: validation error
```

## Database Impact

No new tables. Existing `profiles` table from PROF-01.
`updated_at` must be refreshed on every update.

## Security / Authorization

- Only owner can update their own profile.
- No admin override on this endpoint (admin story is separate).
- Extra/unknown fields rejected by Pydantic (`extra="forbid"`).

## Test Requirements

- Full update (all three fields) saves correctly
- Partial update only changes sent fields
- Bio over 500 chars returns 422
- Unauthenticated returns 401
- `updated_at` is newer after update
- Sending empty body returns 200 with no changes

## Definition of Done

- [ ] `PATCH /api/v1/profiles/me` implemented
- [ ] Partial update works correctly
- [ ] Validation enforced on all fields
- [ ] All acceptance criteria have passing tests
- [ ] Ruff + mypy pass
- [ ] PR merged

---

---

# Story 3 — PROF-03

## Title

**Authenticated user can view a peer's safe profile**

## Epic

`EPIC-02 — User Profile & Language Foundation`

## Feature ID

`PROF-03`

## Milestone

`M2 — Profile + Language Foundation`

## Priority

High

## User Story

As a learner,
I want to view another user's profile,
so that I can learn about a potential language partner before connecting.

## Business Context

Peer profile visibility is required by Matching (to show candidate cards),
Friendship (to display a requester's profile), and Calls (to show the peer during a call).
The peer profile response must never expose auth-owned or private fields.

## In Scope

- `GET /api/v1/profiles/{user_id}` — authenticated user views another user's profile
- Response includes only safe public fields: `user_id`, `bio`, `profession`, `location`, `avatar_url`
- Response must NOT include: email, phone, password, role, account_status, refresh tokens
- Only ACTIVE accounts are viewable — others return 404
- Requester must be authenticated

## Out of Scope

- Language/interest data in this response (delivered by PROF-04, PROF-05)
- Blocking enforcement (delivered by BLOCK domain in M3)
- Viewing own profile through this endpoint (use `GET /profiles/me`)

## Dependencies

```
Blocked by:
  PROF-01 — profiles table must exist

Relates to:
  MATCH-01 — Matching will use the safe profile summary contract
  FRIEND-01 — Friendship will use this endpoint to display requester
```

## Acceptance Criteria

**AC1 — Authenticated user can view an active peer's profile**

Given an authenticated learner
And another user with an ACTIVE account and a completed profile
When they call `GET /api/v1/profiles/{user_id}`
Then the API returns HTTP 200 with safe profile fields.

**AC2 — Non-existent or inactive user returns 404**

Given a user_id that does not exist, or belongs to a SUSPENDED/BLOCKED/DELETED account
When `GET /api/v1/profiles/{user_id}` is called
Then the API returns HTTP 404.

**AC3 — Auth/private fields are never in the response**

Given any valid peer profile response
Then the response does not contain: `email`, `phone_number`, `password_hash`,
`role`, `account_status`, OTP data, or refresh token data.

**AC4 — Unauthenticated request is rejected**

Given no access token
When `GET /api/v1/profiles/{user_id}` is called
Then the API returns HTTP 401.

**AC5 — Own profile can be viewed via this endpoint too**

Given an authenticated learner
When they call `GET /api/v1/profiles/{their_own_user_id}`
Then the API returns HTTP 200 (same safe profile, not the full self-profile).

## Technical Notes

- Return 404 for inactive users, not 403 — do not reveal account status to peers.
- The `PeerProfileResponse` schema is a strict subset of the full self-profile.
- This schema will be reused by Matching as the `SafeProfileSummary` contract.

## API Impact

```
GET /api/v1/profiles/{user_id}
Authorization: Bearer <access_token>

Response 200:
{
  "user_id": 2,
  "bio": "Native Hindi speaker, learning English",
  "profession": "Student",
  "location": "Delhi",
  "avatar_url": null
}

Response 401: unauthenticated
Response 404: user not found or not active
```

## Database Impact

No new tables. Reads from `profiles` + status check against `users.account_status`.
The Profile domain may read `account_status` from the `users` table for this check,
but must never expose it in the response.

## Security / Authorization

- Authenticated users only.
- Auth fields are never serialized into the peer response.
- Inactive account returns 404 — do not reveal suspension/deletion status.

## Test Requirements

- Active peer profile returns 200 with safe fields
- Non-existent user_id returns 404
- Suspended/deleted user returns 404
- Unauthenticated returns 401
- Response schema verified to not contain email, phone, password, role, account_status
- Own profile accessible via this endpoint

## Definition of Done

- [ ] `GET /api/v1/profiles/{user_id}` implemented
- [ ] `PeerProfileResponse` schema contains no auth fields
- [ ] Inactive users return 404
- [ ] All acceptance criteria have passing tests
- [ ] Ruff + mypy pass
- [ ] PR merged

---

---

# Story 4 — PROF-04

## Title

**Learner can add and manage interests**

## Epic

`EPIC-02 — User Profile & Language Foundation`

## Feature ID

`PROF-04`

## Milestone

`M2 — Profile + Language Foundation`

## Priority

High

## User Story

As a learner,
I want to select topics I am interested in,
so that I am matched with peers who share similar interests.

## Business Context

Interests are the primary non-language signal for the matching score in M3.
A learner with interests selected will receive better-quality matches.
Interests are optional for profile completion but strongly encouraged.

## In Scope

- `interests` table — predefined list seeded at startup/migration
- `user_interests` join table — which interests a user has selected
- `GET /api/v1/interests` — list all available predefined interests (public, no auth required)
- `PUT /api/v1/profiles/me/interests` — replace the authenticated user's interest selections
- Response includes selected interest IDs and names
- Predefined seed interests (examples): Music, Travel, Technology, Sports, Movies, Books,
  Cooking, Gaming, Art, Science, Business, Fashion, Nature, Fitness
- Maximum 10 interests per user enforced
- Custom interests: user may submit a free-text interest name (stored separately or normalised)

## Out of Scope

- Matching scoring (M3)
- Interest-based search/filtering (M3)
- Admin management of the interests list
- Deduplication of near-identical custom interests (future)

## Dependencies

```
Blocked by:
  PROF-02 — profiles table and update pattern must exist

Relates to:
  MATCH-01 — Matching reads user interests for scoring
```

## Acceptance Criteria

**AC1 — Learner can list all available interests**

Given any authenticated user
When they call `GET /api/v1/interests`
Then the API returns HTTP 200 with the full predefined interest list.

**AC2 — Learner can set their interests**

Given an authenticated learner
When they call `PUT /api/v1/profiles/me/interests` with a list of up to 10 interest IDs
Then their interest selections are saved
And the API returns HTTP 200 with their selected interests.

**AC3 — PUT replaces all interests**

Given a learner with 3 existing interests
When they call `PUT /api/v1/profiles/me/interests` with 2 different interest IDs
Then only the 2 new interests are saved
And the previous 3 are removed.

**AC4 — More than 10 interests are rejected**

Given an authenticated learner
When they submit 11 or more interest IDs
Then the API returns HTTP 422.

**AC5 — Invalid interest ID is rejected**

Given an interest ID that does not exist in the predefined list
When included in the interests update
Then the API returns HTTP 422.

**AC6 — Clearing all interests is allowed**

Given an authenticated learner
When they call `PUT /api/v1/profiles/me/interests` with an empty list `[]`
Then all interest selections are removed
And the API returns HTTP 200.

## Technical Notes

- `PUT` (full replace) is cleaner than `PATCH` for a flat list — avoids add/remove complexity.
- Seed interests via an Alembic `data migration` or startup seeder — do not hardcode in routes.
- `user_interests` is a join table: `(user_id, interest_id)` with a composite PK.
- Validate all submitted interest IDs exist before writing — reject the whole batch if any is invalid.

## API Impact

```
GET /api/v1/interests
Response 200: [{"id": 1, "name": "Music"}, {"id": 2, "name": "Travel"}, ...]

PUT /api/v1/profiles/me/interests
Authorization: Bearer <access_token>
Body: {"interest_ids": [1, 3, 7]}
Response 200: {"interests": [{"id": 1, "name": "Music"}, ...]}
Response 422: invalid ID or too many interests
```

## Database Impact

```sql
CREATE TABLE interests (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE user_interests (
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interest_id INTEGER NOT NULL REFERENCES interests(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, interest_id)
);
```

Seed data migration for predefined interests.

## Security / Authorization

- Listing interests: no authentication required (public reference data).
- Updating interests: authenticated owner only.
- Interest IDs must be validated server-side — client cannot inject arbitrary values.

## Test Requirements

- List interests returns all seeded interests
- Setting valid interests saves correctly
- PUT replaces previous selections entirely
- 11 interests returns 422
- Invalid interest ID returns 422
- Empty list clears all interests
- Unauthenticated update returns 401

## Definition of Done

- [ ] `interests` and `user_interests` migrations applied
- [ ] Seed data for predefined interests
- [ ] `GET /api/v1/interests` works
- [ ] `PUT /api/v1/profiles/me/interests` works
- [ ] Replace semantics confirmed by test
- [ ] All acceptance criteria have passing tests
- [ ] Ruff + mypy pass
- [ ] PR merged

---

---

# Story 5 — PROF-05

## Title

**Learner can configure native and learning languages with proficiency**

## Epic

`EPIC-02 — User Profile & Language Foundation`

## Feature ID

`PROF-05`

## Milestone

`M2 — Profile + Language Foundation`

## Priority

Critical

## User Story

As a learner,
I want to declare which language I speak natively and which I am learning,
so that the platform can match me with the right conversation partners.

## Business Context

Language configuration is the most critical signal for TalkTribe's core value proposition.
Matching uses it to find compatible learners. Pairing uses it to confirm both users are
practicing the same target language. Profile eligibility (PROF-06) requires at least one
learning language to be set before a user can be matched or paired.

## In Scope

- `languages` reference table — seeded with English for MVP
- `user_languages` join table — user ↔ language with role and proficiency
- Three language roles: `NATIVE`, `FLUENT`, `LEARNING`
- CEFR proficiency levels: `A1`, `A2`, `B1`, `B2`, `C1`, `C2` (not required for NATIVE role)
- `GET /api/v1/languages` — list all supported languages
- `PUT /api/v1/profiles/me/languages` — replace the authenticated user's language configuration
- Response includes the user's full language list with roles and proficiency
- Validation: user must have exactly one NATIVE language
- Validation: user must have at least one LEARNING language (for eligibility, not for this endpoint's 200)
- A user may not have the same language in NATIVE and LEARNING simultaneously

## Out of Scope

- Languages other than English in the seed data for MVP (extensible, but only English seeded)
- Language-based matching scoring (M3)
- Admin management of the language list

## Dependencies

```
Blocked by:
  PROF-02 — profile update pattern must exist

Relates to:
  PROF-06 — Eligibility check requires at least one LEARNING language
  MATCH-01 — Matching reads user_languages for scoring
  PAIR-01 — Pairing checks language compatibility
```

## Acceptance Criteria

**AC1 — Learner can list supported languages**

Given any authenticated user
When they call `GET /api/v1/languages`
Then the API returns HTTP 200 with at least English in the list.

**AC2 — Learner can set native and learning language**

Given an authenticated learner
When they call `PUT /api/v1/profiles/me/languages` with:
  `[{"language_id": 1, "role": "NATIVE"}, {"language_id": 1, "role": "LEARNING", "proficiency": "B2"}]`
Then the configuration is saved
And the API returns HTTP 200 with the saved language list.

**AC3 — Exactly one NATIVE language is required**

Given a user submitting a language list with zero or two NATIVE entries
When `PUT /api/v1/profiles/me/languages` is called
Then the API returns HTTP 422.

**AC4 — LEARNING language requires proficiency**

Given a LEARNING language entry with no proficiency set
When submitted to `PUT /api/v1/profiles/me/languages`
Then the API returns HTTP 422.

**AC5 — Same language cannot be NATIVE and LEARNING simultaneously**

Given a user submitting the same language_id as both NATIVE and LEARNING
When `PUT /api/v1/profiles/me/languages` is called
Then the API returns HTTP 422.

**AC6 — Invalid proficiency value is rejected**

Given a proficiency value outside `A1 A2 B1 B2 C1 C2`
When submitted
Then the API returns HTTP 422.

**AC7 — PUT replaces all language entries**

Given a learner with existing language config
When they submit a new complete language list
Then all previous entries are replaced.

## Technical Notes

- `PUT` (full replace) is correct here — same pattern as interests.
- Validate the entire batch before any write — rollback the whole transaction if invalid.
- `proficiency` column is nullable: NULL is valid for NATIVE, required for LEARNING/FLUENT.
- Language role and proficiency should be Python enums mapped to DB VARCHAR/ENUM.

## API Impact

```
GET /api/v1/languages
Response 200: [{"id": 1, "name": "English", "code": "en"}]

PUT /api/v1/profiles/me/languages
Authorization: Bearer <access_token>
Body:
{
  "languages": [
    {"language_id": 1, "role": "NATIVE"},
    {"language_id": 1, "role": "LEARNING", "proficiency": "B2"}
  ]
}
Response 200:
{
  "languages": [
    {"language_id": 1, "name": "English", "role": "NATIVE", "proficiency": null},
    {"language_id": 1, "name": "English", "role": "LEARNING", "proficiency": "B2"}
  ]
}
Response 422: validation error
```

## Database Impact

```sql
CREATE TABLE languages (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(100) NOT NULL UNIQUE,
    code  VARCHAR(10)  NOT NULL UNIQUE   -- ISO 639-1, e.g. "en"
);

CREATE TABLE user_languages (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language_id  INTEGER     NOT NULL REFERENCES languages(id),
    role         VARCHAR(10) NOT NULL,   -- NATIVE | FLUENT | LEARNING
    proficiency  VARCHAR(5),             -- A1|A2|B1|B2|C1|C2, nullable for NATIVE
    UNIQUE (user_id, language_id, role)
);

CREATE INDEX ix_user_languages_user_id ON user_languages(user_id);
```

Seed data migration: insert English `('English', 'en')`.

## Security / Authorization

- Listing languages: no authentication required.
- Updating languages: authenticated owner only.
- All validation server-side — client cannot inject invalid roles or proficiency values.

## Test Requirements

- List languages returns English
- Setting NATIVE + LEARNING saves correctly
- Zero NATIVE entries returns 422
- Two NATIVE entries returns 422
- LEARNING without proficiency returns 422
- Same language as NATIVE and LEARNING returns 422
- Invalid proficiency string returns 422
- PUT replaces previous language config
- Unauthenticated update returns 401

## Definition of Done

- [ ] `languages` and `user_languages` migrations applied
- [ ] English seeded
- [ ] `GET /api/v1/languages` works
- [ ] `PUT /api/v1/profiles/me/languages` with full validation works
- [ ] All acceptance criteria have passing tests
- [ ] Role and proficiency enums defined
- [ ] Ruff + mypy pass
- [ ] PR merged

---

---

# Story 6 — PROF-06

## Title

**System can evaluate whether a profile is complete (ProfileEligibility)**

## Epic

`EPIC-02 — User Profile & Language Foundation`

## Feature ID

`PROF-06`

## Milestone

`M2 — Profile + Language Foundation`

## Priority

Critical

## User Story

As the TalkTribe matching and pairing system,
I need to know whether a user's profile is complete enough to participate,
so that incomplete or empty profiles are never shown to other learners or placed in a queue.

## Business Context

ProfileEligibility is an internal contract — not a user-facing endpoint.
Matching (M3) calls it to exclude incomplete profiles from candidate results.
Pairing (M5) calls it before allowing a user to join the queue.
Without this contract, a user with an empty profile could appear in matches
or enter a pairing session with no useful identity.

A profile is considered complete when it has:
- At least one `bio` (non-empty)
- At least one `LEARNING` language configured

This is the minimum viable bar for MVP. It may be tightened in later milestones.

## In Scope

- `ProfileEligibilityService` (or function) in the Profile application layer
- Returns a boolean and a reason when the profile is incomplete
- Called by Matching and Pairing — not exposed as a public HTTP endpoint
- Encapsulates the completeness rules so they can be updated in one place

## Out of Scope

- User-facing "profile completion percentage" UI (future)
- Forcing the user to complete profile before any action (that is a route guard, not this service)
- Admin override of eligibility

## Dependencies

```
Blocked by:
  PROF-02 — profile update (bio must be settable)
  PROF-05 — language configuration (LEARNING language must be settable)

Consumed by:
  MATCH-01 — Matching candidate query
  PAIR-01 — Pairing queue join
```

## Acceptance Criteria

**AC1 — Complete profile is eligible**

Given a user with a non-empty bio and at least one LEARNING language
When `ProfileEligibilityService.check(user_id)` is called
Then it returns `eligible=True`.

**AC2 — Missing bio makes profile ineligible**

Given a user with no bio set
When `check(user_id)` is called
Then it returns `eligible=False` with reason `PROFILE_BIO_MISSING`.

**AC3 — Missing learning language makes profile ineligible**

Given a user with a bio but no LEARNING language
When `check(user_id)` is called
Then it returns `eligible=False` with reason `PROFILE_LEARNING_LANGUAGE_MISSING`.

**AC4 — Both missing returns first failing reason**

Given a user with neither bio nor LEARNING language
When `check(user_id)` is called
Then it returns `eligible=False`.

## Technical Notes

- Return a dataclass or simple Pydantic model: `ProfileEligibility(eligible: bool, reason: str | None)`.
- Keep rules in one place — do not scatter eligibility logic across Matching and Pairing.
- This service may be called inside a larger transaction owned by the caller domain.

## API Impact

None — internal service contract only.

## Database Impact

No new tables. Reads from `profiles` and `user_languages`.

## Security / Authorization

Internal service — no HTTP surface. Authorization is the caller domain's responsibility.

## Test Requirements

- User with bio + LEARNING language → eligible
- User with no bio → ineligible, PROFILE_BIO_MISSING
- User with bio but no LEARNING language → ineligible, PROFILE_LEARNING_LANGUAGE_MISSING
- User with neither → ineligible
- Service is importable and callable by Matching and Pairing without circular imports

## Definition of Done

- [ ] `ProfileEligibilityService` implemented in Profile application layer
- [ ] Returns `eligible` + `reason` struct
- [ ] All acceptance criteria have passing tests
- [ ] Matching and Pairing can import and call the service without circular dependency
- [ ] Ruff + mypy pass
- [ ] PR merged

---

---

# Story 7 — PROF-07

## Title

**Learner can upload a profile photo**

## Epic

`EPIC-02 — User Profile & Language Foundation`

## Feature ID

`PROF-07`

## Milestone

`M2 — Profile + Language Foundation`

## Priority

Medium

## User Story

As a learner,
I want to upload a profile photo,
so that other users can recognise me during matches and calls.

## Business Context

Profile photo improves trust and engagement in a language exchange context.
It is optional for profile completion and can be deferred without blocking M3 or M5.
The `avatar_url` column already exists on `profiles` from PROF-01 — this story
implements the upload flow that populates it.

## In Scope

- `POST /api/v1/profiles/me/photo` — multipart file upload
- Accepts JPEG and PNG only, max 5 MB
- Stores the file in object storage (S3-compatible)
- Saves the returned URL to `profiles.avatar_url`
- Returns the updated profile with `avatar_url` populated
- Old photo is deleted from storage when a new one is uploaded

## Out of Scope

- Video profile (future)
- Image resizing / thumbnail generation (future)
- CDN configuration (deployment concern)
- Admin photo moderation (M9)

## Dependencies

```
Blocked by:
  PROF-02 — profiles table + avatar_url column must exist

Requires:
  Object storage infrastructure (S3 or compatible)
  StorageService interface/adapter

OPEN DECISION:
  Object storage provider not yet selected.
  This story is BLOCKED until storage infrastructure is decided.
  Mark as BLOCKED_BY_DECISION until resolved.
```

## Acceptance Criteria

**AC1 — Valid image upload succeeds**

Given an authenticated learner
When they upload a valid JPEG or PNG under 5 MB
Then the file is stored in object storage
And `profiles.avatar_url` is updated with the public URL
And the API returns HTTP 200 with the updated profile.

**AC2 — Oversized file is rejected**

Given a file larger than 5 MB
When submitted to the upload endpoint
Then the API returns HTTP 422.

**AC3 — Invalid file type is rejected**

Given a file that is not JPEG or PNG (e.g. GIF, PDF)
When submitted
Then the API returns HTTP 422.

**AC4 — Uploading a new photo replaces the old one**

Given a learner with an existing photo
When they upload a new photo
Then the old file is deleted from storage
And `avatar_url` is updated to the new URL.

**AC5 — Unauthenticated request is rejected**

Given no access token
When the upload endpoint is called
Then the API returns HTTP 401.

## Technical Notes

- Implement a `StorageService` interface — do not hardcode S3 SDK calls in the route.
- Use a local filesystem adapter for development/testing; S3 adapter for production.
- File names should be namespaced by user ID to avoid collisions: `photos/user_{id}/avatar.jpg`.
- `TRUSTED_PROXY_IPS` production-safety pattern applies here — storage URL may be environment-dependent.

## API Impact

```
POST /api/v1/profiles/me/photo
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
Body: file field

Response 200: updated profile with avatar_url
Response 401: unauthenticated
Response 422: invalid type or size
```

## Database Impact

`profiles.avatar_url` column already exists (created in PROF-01 migration). No new migration needed.

## Security / Authorization

- Authenticated owner only.
- File type validated server-side (check magic bytes, not just extension).
- File size validated before reading entire upload into memory.

## Test Requirements

- Valid JPEG upload saves URL and returns 200
- File over 5 MB returns 422
- Non-image file returns 422
- Second upload deletes old file and updates URL
- Unauthenticated returns 401
- StorageService is mockable for tests (interface pattern)

## Definition of Done

- [ ] `StorageService` interface defined
- [ ] Local filesystem adapter implemented for dev/test
- [ ] S3 adapter implemented for production
- [ ] `POST /api/v1/profiles/me/photo` implemented
- [ ] Old photo deleted on replacement
- [ ] All acceptance criteria have passing tests
- [ ] Ruff + mypy pass
- [ ] PR merged

---

## M2 Implementation Order

Following the roadmap's dependency-first principle:

```
1. PROF-01 — profiles table + GET /profiles/me
        ↓
2. PROF-02 — PATCH /profiles/me (update)
        ↓
3. PROF-03 — GET /profiles/{user_id} (peer view)
        ↓
4. PROF-04 — interests + user_interests
   PROF-05 — languages + user_languages     ← can run in parallel with PROF-04
        ↓
5. PROF-06 — ProfileEligibility contract
        ↓
6. PROF-07 — Profile photo                  ← parallel, deferred until storage decided
```

## M2 Exit Criteria (from roadmap)

- [ ] User can retrieve own profile
- [ ] User can update own profile
- [ ] Authenticated users can view permitted peer profile
- [ ] Private auth fields are never exposed
- [ ] Interests work
- [ ] Custom interests work
- [ ] English exists as supported language
- [ ] A1–C2 works
- [ ] Profile completeness can be evaluated
- [ ] Matching-safe profile summary contract exists
- [ ] Pairing can ask whether profile is complete
- [ ] Profile/Language tests pass
