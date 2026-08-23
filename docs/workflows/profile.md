# TalkTribe Profile Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** User / Profile  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `TARGET_ARCHITECTURE.md`, `DATABASE_ARCHITECTURE.md`, `API_ARCHITECTURE.md`, `SECURITY_ARCHITECTURE.md`, `AUTHENTICATION_WORKFLOW.md`

---

# 1. Purpose

This document defines the end-to-end Profile workflow for TalkTribe MVP.

It covers:

- initial profile creation
- mandatory and optional fields
- profile completion
- profile editing
- profile photo upload
- interests
- language/profile linkage
- authenticated profile viewing
- privacy and field exposure
- profile validation
- profile completion checks required by Matching and Pairing
- dependencies on Auth, Language, Matching, Friendship, Calls, and Admin
- failure cases
- testing
- Definition of Done

---

# 2. Profile Goal

The profile should provide enough information for:

```text
User identity presentation
        ↓
Language-learning context
        ↓
Matching
        ↓
Peer discovery
        ↓
Pairing
        ↓
Voice conversation
```

The profile is not authentication data.

Authentication answers:

```text
Who is the account?
```

Profile answers:

```text
How should this learner appear and participate in TalkTribe?
```

---

# 3. Profile Availability

A user may register and verify their account before completing the profile.

Primary flow:

```text
Register
   ↓
Verify Email
   ↓
Login
   ↓
No completed profile
   ↓
Profile setup required
   ↓
Complete mandatory profile data
   ↓
Profile becomes eligible for discovery/pairing
```

A verified user may access limited account/setup functionality before completing the profile.

They should not be considered fully eligible for matching or automatic pairing until required profile information exists.

---

# 4. Profile Fields

Current MVP profile model includes or is expected to include:

## Profile Header

```text
Profile Photo
Name / Full Name
Username
```

## Stats

```text
Calls
Friends / Peers
Call Time
Rating
```

## About Me

```text
Bio
Profession
Location
Interests
```

## Language Profile

```text
Mother Tongue
Languages I Speak
Language I Want to Learn
Current Level
```

## Future sections

Not part of current MVP profile behavior:

```text
Conversation Preferences
Achievements
Rewards
```

These should not drive current database/API complexity unless an MVP requirement later needs a field from them.

---

# 5. Mandatory vs Optional Fields

Current product decision:

Optional in MVP:

```text
Profile Photo
Bio
Profession
Location
```

All other required MVP profile fields are mandatory once finalized.

At minimum the profile setup should require enough data for:

```text
identity display
language profile
proficiency
interests
matching eligibility
```

---

# 6. Profile Completion

Profile completion should be an explicit application concept.

Recommended:

```text
profile_complete = derived state
```

Do not necessarily persist a boolean if it can be safely derived from required fields.

Conceptual rule:

```text
ProfileComplete(user)
=
all mandatory profile fields exist
AND
required language information exists
AND
required interests/learning data is valid
```

---

# 7. Initial Profile Setup — Happy Path

```text
User logs in after verification
        ↓
GET /api/v1/profiles/me
        ↓
Profile not found / incomplete
        ↓
Frontend opens setup form
        ↓
User provides required fields
        ↓
PATCH /api/v1/profiles/me
        ↓
API validates basic field format
        ↓
Application validates:
- authenticated owner
- mandatory fields
- allowed language/proficiency
- valid interests
        ↓
BEGIN TRANSACTION
        ↓
Create/update profile
        ↓
Create/update user interests
        ↓
Create/update language relations
        ↓
COMMIT
        ↓
Recalculate profile-complete state
        ↓
Return completed profile
```

---

# 8. Ownership

Only the account holder can modify their normal profile.

```text
Current user ID
      ↓
Profile user ID
      ↓
must match
```

Admin may have separate moderation/edit capabilities only if explicitly defined.

Do not allow:

```text
PATCH /profiles/{other_user_id}
```

for normal users.

---

# 9. Get Own Profile

Recommended endpoint:

```text
GET /api/v1/profiles/me
```

Returns the authenticated user's complete self-view.

Self-view may include fields that are not exposed to other learners.

Example categories:

```text
profile fields
language configuration
interests
stats
profile completion state
settings relevant to profile
```

Do not include authentication secrets.

---

# 10. View Another User Profile

Recommended endpoint:

```text
GET /api/v1/profiles/{user_id}
```

Final visibility decision:

```text
Unauthenticated user → denied
Authenticated learner → permitted public/authenticated profile view
Admin → view according to admin policy
```

The returned schema should be:

```text
PublicProfileResponse
```

not the same schema as the internal/self profile.

---

# 11. Public / Authenticated Profile Fields

Likely fields visible to other authenticated learners:

```text
user_id
username
full_name / display name
profile photo
bio
profession
location
interests
language information
proficiency
rating
call/friend stats where product allows
```

Must never expose:

```text
email
phone number
password hash
OTP data
refresh tokens
internal account security fields
admin notes
private moderation details
```

Exact field list should be finalized before Profile API implementation.

---

# 12. Profile Editing

Recommended:

```text
PATCH /api/v1/profiles/me
```

Flow:

```text
Authenticated user
        ↓
Submit changed fields
        ↓
API validation
        ↓
Profile application service
        ↓
Ownership check
        ↓
Business validation
        ↓
Update profile-owned data
        ↓
Commit
        ↓
Return updated profile
```

Use PATCH for partial changes.

PUT may be added only if complete replacement semantics are genuinely needed.

---

# 13. Username Changes

Username currently belongs to account identity.

Do not silently treat username as a normal profile field.

If username changes are supported later:

```text
Auth/User identity workflow
```

should own uniqueness/security implications.

For MVP, username may be read-only after registration unless explicitly decided otherwise.

---

# 14. Full Name Ownership

Current system stores `full_name` in the existing user/auth model.

Target architecture prefers user-facing profile data in Profile.

Migration strategy:

```text
existing full_name
    ↓
preserve behavior
    ↓
move or expose through Profile boundary incrementally
```

Do not break current registration simply to achieve perfect separation immediately.

---

# 15. Profile Photo Workflow

Profile photo is optional.

Recommended flow:

```text
User selects image
        ↓
POST /api/v1/profiles/me/photo
        ↓
Authenticate owner
        ↓
Validate:
- file size
- file type
- file signature/content
        ↓
StorageService
        ↓
Object storage
        ↓
Receive object key/URL
        ↓
Update profile photo reference
        ↓
Return updated profile
```

PostgreSQL stores metadata/reference.

Object storage stores the actual file.

---

# 16. Profile Photo Replacement

When replacing a photo:

```text
upload new photo
   ↓
successfully store
   ↓
update DB reference
   ↓
optionally delete old object
```

Do not delete the old object before the new upload succeeds.

---

# 17. Interests

Current decision:

- predefined interests exist
- user may add custom interests

Examples include:

```text
Hiking
Yoga
Cycling
Photography
Playing Guitar
Reading
Chess
Traveling
Video Gaming
Gardening
Music Production
...
```

---

# 18. Interest Selection Flow

```text
Profile setup/edit
        ↓
GET available predefined interests
        ↓
User selects existing interests
        ↓
User may add custom interest
        ↓
Normalize names
        ↓
Validate duplicates/limits
        ↓
Persist interests
        ↓
Persist user-interest relations
```

---

# 19. Interest Normalization

Avoid duplicates such as:

```text
Photography
photography
 PHOTOGRAPHY
```

Normalize for uniqueness while preserving a display-friendly name.

Exact normalization strategy belongs to implementation.

---

# 20. Custom Interest Safety

Custom interests may create moderation concerns.

MVP should at least:

```text
trim whitespace
limit length
reject empty values
avoid obvious duplicate values
```

Admin moderation of custom interests can be added if required.

Do not overbuild moderation before there is a concrete need.

---

# 21. Language Information

Profile setup requires language information.

Current MVP:

```text
supported practice language = English
```

Proficiency:

```text
A1
A2
B1
B2
C1
C2
```

Language master-data validation belongs to Language.

Profile owns the user-facing setup workflow.

---

# 22. Language Setup Flow

```text
User opens profile setup
        ↓
Load supported languages
        ↓
Select:
- mother tongue
- language spoken
- English learning/practice target
- proficiency
        ↓
Validate against Language domain
        ↓
Persist user-language relations
        ↓
Profile completion recalculated
```

---

# 23. MVP Language Simplification

Because MVP only supports English practice:

```text
practice_language = English
```

may be implicitly fixed in the UI.

However the database/domain should still support additional languages later.

Do not hardcode the entire architecture around a permanent English-only system.

---

# 24. Proficiency

User self-selects their current level.

Allowed:

```text
A1
A2
B1
B2
C1
C2
```

Current product direction also mentions feedback/rating influencing learner understanding later.

For MVP:

```text
self-selected level
```

is sufficient for profile and matching.

Do not automatically overwrite it from feedback unless a future requirement explicitly says so.

---

# 25. Profile Stats

Profile may display:

```text
Calls
Friends / Peers
Call Time
Rating
```

Prefer deriving these from authoritative records:

```text
Calls → voice_calls
Friends → friendships
Call Time → voice-call durations
Rating → call_feedback aggregation
```

Avoid storing duplicated counters unless performance measurements later justify cached/denormalized stats.

---

# 26. Rating Display

User rating may be shown on profile.

Recommended derived model:

```text
average rating
rating count
```

Do not expose individual reviewer identity unless product requirements explicitly allow it.

Exact formula is finalized in Feedback workflow.

---

# 27. Profile and Matching

Matching needs profile summaries.

Matching should not import Profile repositories directly.

Expose something like:

```text
ProfileReader
```

with only the required matching fields.

Conceptual summary:

```text
user_id
language/proficiency
interests
profession
location/country if used
profile eligibility
```

---

# 28. Profile and Pairing

Automatic pairing should require:

```text
verified account
active account
completed profile
valid language information
eligible for communication
```

Flow:

```text
pairing.join
   ↓
ProfileEligibility check
   ↓
complete?
   ├── No → PROFILE_INCOMPLETE
   └── Yes → continue
```

---

# 29. Profile and Friendship

Friendship may consume a minimal safe user summary:

```text
user_id
display name
photo
```

It should not query profile internals directly.

---

# 30. Profile and Calls

Call screens may need:

```text
display name
profile photo
rating
language/proficiency
```

Expose a dedicated profile summary contract.

Do not let Call domain depend on full Profile persistence.

---

# 31. Profile and Admin

Admin may need:

```text
user/profile overview
moderation context
reported profile data
```

Admin should use a deliberate management/read contract.

Admin should not directly edit profile tables merely because it is privileged.

---

# 32. Profile Privacy

Profile information is visible only to authenticated users under current product rules.

However different profile fields may have different sensitivity.

Classify fields:

## Authenticated-public

Safe for another learner.

## Self-only

Visible only to account owner.

## Admin-only

Moderation/internal data.

This classification should be encoded through response schemas and authorization.

---

# 33. Blocked User Profile Behavior

Current blocking decision:

```text
blocked user cannot interact
```

Exact visibility after blocking remains partially open.

Recommended safe direction:

```text
blocked relationship
→ no messaging
→ no calls
→ no friend request
→ no matching
```

Whether the blocked user can still view the basic profile should be explicitly finalized later.

Do not silently invent it in code.

---

# 34. Profile Error Codes

Recommended:

```text
PROFILE_NOT_FOUND
PROFILE_INCOMPLETE
PROFILE_VALIDATION_FAILED
PROFILE_UPDATE_NOT_ALLOWED
INVALID_INTEREST
INVALID_LANGUAGE
INVALID_PROFICIENCY
PROFILE_PHOTO_INVALID
PROFILE_PHOTO_TOO_LARGE
```

---

# 35. Profile Transaction Boundaries

For profile updates affecting multiple tables:

```text
BEGIN
  update profile
  update interests
  update language relations
COMMIT
```

This ensures a profile is not partially updated.

File upload may happen before/around the DB transaction.

Avoid keeping a DB transaction open during long object-storage network operations.

---

# 36. Profile Deletion

Account deletion should cascade/remove profile-owned data according to final deletion policy.

Profile-owned records:

```text
profiles
user_interests
profile image reference
possibly user_languages depending final ownership
```

Object storage cleanup should also occur.

Exact audit/report retention conflict remains outside Profile and must follow Account Deletion policy.

---

# 37. Profile API Surface

Recommended:

```text
GET   /api/v1/profiles/me
PATCH /api/v1/profiles/me
GET   /api/v1/profiles/{user_id}
POST  /api/v1/profiles/me/photo
DELETE /api/v1/profiles/me/photo
PUT   /api/v1/profiles/me/languages
```

Potential interest endpoints:

```text
GET /api/v1/interests
```

or expose predefined interests through a reference-data endpoint.

Exact route ownership can be adjusted without changing workflow behavior.

---

# 38. Profile Frontend Flow

```text
Login success
   ↓
Fetch self profile
   ↓
Profile complete?
   ├── No
   │     ↓
   │  Profile Setup Page
   │     ↓
   │  Complete required fields
   │     ↓
   │  Save
   │     ↓
   │  Home / discovery
   │
   └── Yes
         ↓
      Home / discovery
```

---

# 39. Editing Frontend Flow

```text
Profile page
   ↓
Edit Profile
   ↓
Load current profile
   ↓
Change fields
   ↓
Validate locally
   ↓
Submit
   ↓
Backend validates
   ↓
Updated profile
```

Frontend validation improves UX but backend remains authoritative.

---

# 40. Failure Scenarios

## Storage upload fails

```text
do not update profile photo reference
return upload error
```

## Database update fails

```text
rollback profile changes
```

## Invalid custom interest

```text
reject only according to validation rules
```

## Invalid proficiency

```text
422 / INVALID_PROFICIENCY
```

## Unauthenticated access

```text
401
```

## User tries to edit another profile

```text
403
```

---

# 41. Testing Workflow

## Profile creation

- create valid profile
- missing mandatory fields
- optional fields omitted
- invalid data rejected

## Ownership

- user edits own profile
- user cannot edit another profile

## Viewing

- authenticated user views another permitted profile
- unauthenticated viewer denied
- private fields absent from response

## Interests

- predefined interest selection
- custom interest creation
- duplicate normalized interest handling

## Language

- valid proficiency
- invalid proficiency
- English MVP configuration
- profile incomplete without required language data

## Photo

- valid image
- invalid type
- oversized image
- storage failure

## Integration

- completed profile becomes eligible for matching/pairing
- incomplete profile is rejected from pairing

---

# 42. Definition of Done — Profile

Profile is ready for dependent MVP features when:

- [ ] Authenticated user can retrieve own profile.
- [ ] User can create/complete profile.
- [ ] User can update own profile.
- [ ] User cannot modify another profile.
- [ ] Authenticated learner can view permitted fields of another profile.
- [ ] Unauthenticated user cannot view protected profiles.
- [ ] Optional/mandatory fields follow agreed rules.
- [ ] English language profile works.
- [ ] A1–C2 proficiency validation works.
- [ ] Predefined interests work.
- [ ] Custom interests work.
- [ ] Profile photo upload is safe and optional.
- [ ] Private auth fields never appear in profile responses.
- [ ] Profile completion can be evaluated.
- [ ] Matching can consume profile summary through a contract.
- [ ] Pairing can check profile eligibility.
- [ ] Profile tests pass.

---

# 43. Dependencies on Profile

Profile is foundational for:

```text
Language setup
Matching
Friendship presentation
Pairing eligibility
Voice-call UI
Ratings display
Admin moderation context
```

Recommended implementation order:

```text
Auth stabilized
   ↓
Profile
   ↓
Language
   ↓
Matching
```

---

# 44. Profile Workflow Diagram

```text
                     AUTHENTICATED USER
                            │
                            ▼
                      FETCH PROFILE
                            │
                  ┌─────────┴─────────┐
                  │                   │
             INCOMPLETE            COMPLETE
                  │                   │
                  ▼                   ▼
             SETUP PROFILE        VIEW / EDIT
                  │
        ┌─────────┼──────────┐
        │         │          │
        ▼         ▼          ▼
     DETAILS   INTERESTS   LANGUAGE
        │         │          │
        └─────────┼──────────┘
                  ▼
             VALIDATE RULES
                  │
                  ▼
              TRANSACTION
                  │
                  ▼
            PROFILE COMPLETE
                  │
         ┌────────┼─────────┐
         ▼        ▼         ▼
      MATCHING  PAIRING   FRIENDSHIP
```

---

# 45. Next Workflow

```text
AUTHENTICATION_WORKFLOW.md      ✅
PROFILE_WORKFLOW.md             ✅
        ↓
LANGUAGE_WORKFLOW.md            ← NEXT
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
