# TalkTribe Matching Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** Matching / Discovery  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `TARGET_ARCHITECTURE.md`, `PROFILE_WORKFLOW.md`, `LANGUAGE_WORKFLOW.md`, `FRIENDSHIP_WORKFLOW.md` when implemented, `SECURITY_ARCHITECTURE.md`

---

# 1. Purpose

This document defines the end-to-end matching workflow for TalkTribe MVP.

It covers:

- who is eligible for matching
- required profile/language data
- candidate discovery
- exclusion rules
- blocking rules
- rule-based compatibility
- interest/profession/hobby influence
- proficiency considerations
- recommendation ranking
- maximum result count
- matching vs live pairing
- API behavior
- caching direction
- failure cases
- testing
- Definition of Done

Matching answers:

```text
Which users are compatible with this learner?
```

It does not answer:

```text
Which compatible learner should I connect to right now?
```

That is the responsibility of the Pairing workflow.

---

# 2. MVP Matching Decision

Current product decision:

```text
MVP matching is rule-based.
```

Future:

```text
AI / embedding-based matching
```

may augment or replace the scoring engine.

For MVP, matching must remain:

```text
deterministic
explainable
testable
low-cost
```

---

# 3. Matching Goals

The matching system should:

1. return only eligible users
2. exclude blocked users
3. avoid returning the requesting user
4. use language compatibility
5. use interests as a primary factor
6. consider hobbies/profession where profile data exists
7. consider proficiency when the matching policy requires it
8. return at most 20 candidates
9. never expose sensitive account data
10. provide deterministic behavior for the same inputs/rules

---

# 4. Matching vs Pairing

These concepts must remain separate.

## Matching

```text
User profile
   ↓
Candidate discovery
   ↓
Compatibility scoring
   ↓
Ranked recommendations
```

Output:

```text
up to 20 compatible users
```

## Pairing

```text
User wants to talk now
   ↓
Check realtime availability
   ↓
Use compatibility + waiting queue
   ↓
Connect one compatible available user
```

Output:

```text
one live peer connection candidate
```

Matching is mostly based on durable profile data.

Pairing adds realtime availability and queue state.

---

# 5. Matching Entry Point

Recommended endpoint:

```text
GET /api/v1/matches
```

Request requires:

```text
authenticated user
active account
verified account
completed profile
valid language profile
```

If these requirements are not met, matching should not proceed.

---

# 6. Matching Eligibility — Requesting User

Before candidate discovery:

```text
Authenticate
   ↓
Account ACTIVE?
   ↓
Verified?
   ↓
Profile complete?
   ↓
Language configuration valid?
   ↓
Eligible for matching?
```

Possible failures:

```text
AUTHENTICATION_REQUIRED
ACCOUNT_NOT_ALLOWED
PROFILE_INCOMPLETE
LANGUAGE_PROFILE_INCOMPLETE
```

---

# 7. Candidate Eligibility

A candidate must satisfy at least:

```text
candidate != requester
candidate account ACTIVE
candidate verified
candidate profile complete
candidate language setup valid
candidate not blocked in either direction
candidate eligible for discovery
```

Additional criteria may later include:

```text
user privacy preference
recent interaction exclusions
country preference
availability
```

but only when explicitly approved.

---

# 8. Blocking Exclusion

Blocking is a hard exclusion.

If:

```text
A blocked B
```

or:

```text
B blocked A
```

then:

```text
A and B must not be recommended to each other.
```

Matching should consume a Friendship/Block eligibility contract.

Forbidden:

```text
Matching → FriendshipRepository
```

Allowed:

```text
Matching → InteractionEligibility contract
```

---

# 9. Candidate Discovery Flow

```text
GET /matches
     ↓
Resolve requester identity
     ↓
Validate profile eligibility
     ↓
Load safe matching profile summary
     ↓
Load candidate summaries
     ↓
Filter ineligible candidates
     ↓
Apply block rules
     ↓
Apply language compatibility
     ↓
Calculate rule-based score
     ↓
Sort by score
     ↓
Apply stable tie-breaker
     ↓
Return maximum 20
```

---

# 10. Matching Data Inputs

The matching engine may consume:

## Profile

```text
user_id
interests
profession
location/country if enabled
profile completeness
```

## Language

```text
practice language
mother tongue
proficiency
spoken languages
```

## Friendship / Blocking

```text
blocked?
already friend?
request state if relevant
interaction eligibility
```

## Optional Presence

Presence is not required for discovery recommendations.

Presence becomes important for live pairing.

---

# 11. Interests as Primary Factor

Current product decision:

```text
Interests are the primary matching factor.
```

Therefore shared interests should have a strong influence on compatibility.

Example:

```text
User A interests:
Photography
Chess
Traveling

User B interests:
Photography
Traveling
Cooking

Shared:
Photography
Traveling
```

This should score better than a candidate with no shared interests, all else being equal.

---

# 12. Hobbies

Hobbies are effectively represented through interests in the current model.

Examples:

```text
Hiking
Gaming
Music
Photography
Cooking
Cycling
```

Do not create a separate Hobby domain unless product requirements later require different semantics.

---

# 13. Profession

Profession may influence compatibility when both users provide it.

Example:

```text
Software Engineer
Software Engineer
```

or related professions may create additional context for conversation.

Because profession is optional, missing profession must not make a user ineligible.

---

# 14. Proficiency

Current allowed values:

```text
A1
A2
B1
B2
C1
C2
```

The exact matching policy is still open.

Possible future strategies include:

```text
prefer same level
prefer nearby level
mix stronger/weaker learners
```

Do not invent a permanent proficiency formula before the product decision is finalized.

For MVP, proficiency may be used as:

```text
a modest ranking signal
```

rather than a hard exclusion unless explicitly approved.

---

# 15. Language Compatibility

MVP practice language:

```text
English
```

Therefore both requester and candidate must be eligible for English practice.

Future multilingual matching:

```text
requester target language
        ↓
candidate compatible language profile
```

should fit the same workflow.

---

# 16. Recommended MVP Scoring Shape

The exact weights are intentionally not finalized.

Conceptually:

```text
compatibility_score =
    interest_score
  + profession_score
  + proficiency_score
  + optional_future_signals
```

Where:

```text
interest_score = primary signal
profession_score = secondary signal
proficiency_score = secondary/modest signal
```

Blocking and account eligibility are not scores.

They are hard filters.

---

# 17. Hard Filters vs Soft Scores

## Hard filters

If false, candidate is removed:

```text
not self
active
verified
profile complete
supported language
not blocked
allowed by discovery/privacy rules
```

## Soft scoring

Candidate remains eligible but rank changes:

```text
shared interests
profession similarity
proficiency compatibility
future preferences
```

This distinction should remain explicit in code.

---

# 18. Stable Tie-Breaking

Two candidates may receive the same score.

Use a stable tie-breaker.

Possible safe options:

```text
profile/user ID
recent recommendation history
deterministic secondary ordering
```

Random ordering may be introduced later if product wants variety.

Do not create nondeterministic behavior that makes tests unreliable without a reason.

---

# 19. Maximum Results

Current product decision:

```text
maximum recommendations = 20
```

Backend must enforce this.

Even if client sends:

```text
limit=1000
```

the service must cap results.

Conceptual:

```text
requested_limit = min(client_limit, 20)
```

---

# 20. Matching Response

Recommended safe shape:

```json
{
  "items": [
    {
      "user_id": 123,
      "display_name": "Example",
      "profile_photo_url": null,
      "proficiency_level": "B1",
      "shared_interests": ["Photography", "Chess"],
      "profession": "Developer",
      "compatibility_score": 82
    }
  ],
  "count": 1
}
```

Do not expose:

```text
email
phone
password/security state
OTP
refresh tokens
admin notes
block internals
```

---

# 21. Recommendation Explanation

Because MVP matching is rule-based, it can optionally explain why a user was suggested.

Example:

```text
"3 shared interests"
"similar proficiency"
"same profession"
```

This can improve user trust.

However explanation format is optional and should not block core matching.

---

# 22. Search vs Matching

Current product requirements also mention user search and filters.

Keep these concepts separate:

## Search

```text
Find users matching explicit query/filter.
```

## Matching

```text
Recommend users based on compatibility.
```

Search may use:

```text
username
country
language
```

Matching uses:

```text
compatibility rules
```

They may share query infrastructure but should not become one confused use case.

---

# 23. Country Filter

Original requirements mention country filtering.

Current profile has:

```text
location
```

but exact country structure is not fully finalized.

Do not build country filtering against arbitrary free-text location unless the data model supports reliable country values.

If country filter is needed, introduce a normalized country field/reference first.

---

# 24. Matching and Friendships

Possible candidate relationship states:

```text
stranger
pending request
friend
blocked
```

Blocked:

```text
exclude
```

Friend:

May be either:

```text
included
or
excluded from discovery recommendations
```

depending on final product policy.

This is still open.

Do not silently exclude friends unless agreed.

---

# 25. Matching and Pending Friend Requests

If A already sent a request to B, the UI may want to show:

```text
request_pending = true
```

rather than suggesting another friend-request action.

This can be supplied through a safe Friendship contract.

It should not affect core compatibility unless product says it should.

---

# 26. Matching and Presence

Discovery recommendations do not require the candidate to be online.

Example:

```text
GET /matches
```

may return compatible offline users.

Live pairing does require availability.

This distinction prevents matching from depending heavily on Redis.

---

# 27. Matching and Automatic Pairing

Pairing can consume matching compatibility.

Conceptually:

```text
User joins pairing queue
   ↓
load waiting candidates
   ↓
hard eligibility filters
   ↓
matching score
   ↓
choose best eligible available candidate
```

Do not duplicate a different compatibility algorithm inside Pairing.

Use the same Matching scoring policy or an explicitly published compatibility service.

---

# 28. Recently Matched Users

Future product option:

```text
avoid immediately pairing same users repeatedly
```

This is not yet finalized.

If added, treat it as a pairing/recommendation freshness rule rather than altering the core user relationship.

---

# 29. Matching Persistence

Do not create a permanent `matches` table for MVP unless historical recommendations become a requirement.

Recommended MVP:

```text
calculate recommendations on demand
```

Potential later optimization:

```text
Redis cache
```

for short-lived matching results.

---

# 30. Caching

At initial scale:

```text
~50 users
```

matching can query PostgreSQL directly with proper indexes.

Redis caching should be added only when useful.

Potential cache:

```text
matches:user:{user_id}
```

with short TTL.

Cache must be invalidated or allowed to expire after profile/interest/language changes.

---

# 31. Matching Query Strategy

Avoid N+1 queries.

Candidate discovery should load the required matching data efficiently.

Possible approach:

```text
candidate IDs
   ↓
batch profile summaries
   ↓
batch interests
   ↓
batch language info
   ↓
score in application layer
```

At MVP scale, prioritize clear code and correct indexes before complex SQL ranking.

---

# 32. Matching Repository Boundaries

Matching may have little or no persistence of its own.

It should consume query contracts.

Examples:

```text
ProfileMatchingReader
LanguageMatchingReader
InteractionEligibility
```

Do not create a generic repository that bypasses all domain ownership merely for convenience.

---

# 33. Authorization

Matching requires:

```text
authenticated user
verified
active account
completed profile
```

Users can request recommendations only for themselves.

Do not allow:

```text
GET /matches?for_user=someone_else
```

for normal users.

Admin has no need to impersonate matching in MVP unless an explicit support feature is added.

---

# 34. Matching Failure Cases

## Profile incomplete

```text
PROFILE_INCOMPLETE
```

## Language setup missing

```text
LANGUAGE_PROFILE_INCOMPLETE
```

## Account not active

```text
ACCOUNT_NOT_ALLOWED
```

## No candidates

Return:

```json
{
  "items": [],
  "count": 0
}
```

This is not an internal server error.

## Data dependency unavailable

If required database data cannot be loaded:

```text
service/internal error
```

Do not return fabricated recommendations.

---

# 35. Privacy

Matching must use only data required for compatibility.

It must not consume:

```text
password data
phone number
email
OTP
refresh tokens
admin notes
private security state
```

Matching summaries should be explicit DTOs/contracts.

---

# 36. Abuse / Enumeration

Do not allow users to exploit Matching as a full account directory exposing every user.

Controls:

```text
authentication
maximum 20 results
safe profile summary
approved filters only
no private data
```

Search functionality should also be separately protected.

---

# 37. API Flow

```text
GET /api/v1/matches?limit=20
        ↓
API auth dependency
        ↓
MatchingApplication.get_matches(current_user)
        ↓
Validate requester
        ↓
Load matching profile
        ↓
Load candidates
        ↓
Hard filter
        ↓
Score
        ↓
Rank
        ↓
Limit 20
        ↓
Map to MatchCandidateResponse
        ↓
200 OK
```

---

# 38. Frontend Flow

```text
User opens Discover
        ↓
GET /matches
        ↓
Loading
        ↓
Candidates returned?
   ├── Yes
   │     ↓
   │  Show match cards
   │     ↓
   │  View profile
   │  Send friend request
   │  Call/connect if eligible
   │
   └── No
         ↓
      Show:
      "No suitable matches found right now."
```

---

# 39. Matching Card

Possible card data:

```text
photo
display name
English level
shared interests
profession
compatibility indication
online status if separately allowed
friend-request state
```

Do not make UI dependent on raw internal score unless product wants that score visible.

---

# 40. Matching Tests

## Eligibility

- authenticated complete user can request matches
- unauthenticated denied
- incomplete profile rejected
- inactive account rejected

## Filtering

- self excluded
- blocked candidate excluded
- candidate with incomplete profile excluded
- unsupported/inactive candidate excluded

## Scoring

- more shared interests ranks higher under configured rules
- profession signal applied when present
- missing optional profession does not exclude candidate
- deterministic result for identical inputs

## Limit

- no more than 20 returned
- client cannot bypass max limit

## Privacy

- private account fields absent

## Integration

- Profile contract used
- Language contract used
- Friendship/block eligibility used
- Pairing can reuse compatibility logic

---

# 41. Definition of Done — Matching

Matching is ready when:

- [ ] Authenticated active user can request recommendations.
- [ ] Incomplete profile cannot use Matching.
- [ ] English-practice eligibility is validated.
- [ ] Self is excluded.
- [ ] Blocked users are excluded in both directions.
- [ ] Ineligible accounts are excluded.
- [ ] Interests are the primary ranking factor.
- [ ] Optional profession/hobby data can influence ranking.
- [ ] Proficiency handling follows approved policy.
- [ ] Results are deterministic/testable.
- [ ] Maximum 20 results is enforced server-side.
- [ ] Safe profile summaries are returned.
- [ ] Sensitive account data is never returned.
- [ ] Cross-domain access uses contracts, not foreign repositories.
- [ ] No unnecessary permanent matches table is required.
- [ ] Automated tests pass.
- [ ] Pairing can reuse Matching compatibility logic.

---

# 42. Open Matching Decisions

Still to finalize:

1. Exact scoring weights.
2. Exact proficiency compatibility rule.
3. Whether existing friends are included in recommendations.
4. Whether pending friend-request users remain in recommendations.
5. Exact country-filter data model.
6. Whether compatibility score is shown to users.
7. Whether recommendation explanations are shown.
8. Whether recently matched users are temporarily deprioritized.
9. Tie-breaking policy.
10. Whether availability affects discovery recommendations or only pairing.

These should remain explicit rather than being guessed during implementation.

---

# 43. Matching Workflow Diagram

```text
                    AUTHENTICATED USER
                           │
                           ▼
                   REQUEST MATCHES
                           │
                           ▼
                 PROFILE COMPLETE?
                           │
                           ▼
                LANGUAGE VALID/ENGLISH
                           │
                           ▼
                 LOAD CANDIDATES
                           │
                           ▼
                     HARD FILTERS
              ┌────────────┼────────────┐
              │            │            │
            SELF       INACTIVE      BLOCKED
              │            │            │
              └─────── EXCLUDED ────────┘
                           │
                           ▼
                      SCORE USERS
                   ┌───────┼────────┐
                   │       │        │
               INTERESTS PROFESSION LEVEL
                   │       │        │
                   └───────┼────────┘
                           ▼
                         RANK
                           │
                           ▼
                     LIMIT TO 20
                           │
                           ▼
                SAFE MATCH SUMMARIES
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
              DISCOVERY           PAIRING
                                  (later,
                               realtime use)
```

---

# 44. Next Workflow

```text
AUTHENTICATION_WORKFLOW.md      ✅
PROFILE_WORKFLOW.md             ✅
LANGUAGE_WORKFLOW.md            ✅
MATCHING_WORKFLOW.md            ✅
        ↓
FRIENDSHIP_WORKFLOW.md          ← NEXT
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
