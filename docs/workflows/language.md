# TalkTribe Language Workflow

**Stage:** 3 — Application Workflows  
**Status:** Workflow baseline  
**Domain:** Language / Reference Data  
**Depends on:** `REQUIREMENTS_BASELINE.md`, `TARGET_ARCHITECTURE.md`, `DATABASE_ARCHITECTURE.md`, `PROFILE_WORKFLOW.md`

---

# 1. Purpose

This document defines the language-related workflow for TalkTribe MVP.

It covers:

- supported languages
- English-only MVP behavior
- mother tongue
- languages spoken
- language being learned/practiced
- CEFR proficiency levels
- user-language relationships
- profile integration
- matching integration
- validation
- future multilingual expansion
- testing
- Definition of Done

The Language domain should remain lightweight in MVP.

---

# 2. MVP Language Decision

Current product decision:

```text
TalkTribe MVP supports English practice only.
```

This means:

```text
practice / learning language = English
```

for MVP users.

However, the architecture must support more languages later without redesigning the whole application.

---

# 3. Language Domain Goal

The Language domain answers:

```text
Which languages does the platform support?
Which languages does this user speak?
Which language is this user learning?
What is their proficiency level?
```

It does not own:

```text
authentication
profile presentation
matching score
friendship
messaging
calls
```

---

# 4. Language Master Data

Recommended durable table:

```text
languages
```

Example MVP row:

```text
code = en
name = English
is_active = true
```

Future examples:

```text
hi → Hindi
es → Spanish
fr → French
de → German
ja → Japanese
```

Do not hardcode future languages only in frontend constants.

---

# 5. User Language Relationship

Recommended relationship model:

```text
user_languages
```

Each relation should represent:

```text
user
language
relationship type
proficiency
```

Possible relationship types:

```text
NATIVE
SPEAKS
LEARNING
```

---

# 6. Current Profile Language Fields

Current product profile includes:

```text
Mother Tongue
Languages Spoken
Language to Learn
Current Level
```

These should map to language-domain data rather than unrelated free-text fields where practical.

---

# 7. CEFR Proficiency Levels

Current product decision:

```text
A1
A2
B1
B2
C1
C2
```

Meaning at a high level:

```text
A1 → beginner
A2 → elementary
B1 → intermediate
B2 → upper intermediate
C1 → advanced
C2 → proficient
```

TalkTribe should use the codes:

```text
A1, A2, B1, B2, C1, C2
```

as canonical application values.

---

# 8. MVP Language Setup — Happy Path

```text
Authenticated user
        ↓
Profile setup
        ↓
Load supported languages
        ↓
User selects mother tongue
        ↓
User selects language(s) spoken if required
        ↓
Learning/practice language fixed to English
        ↓
User selects CEFR level
        ↓
Validate language IDs/codes
        ↓
Validate proficiency
        ↓
BEGIN TRANSACTION
        ↓
Persist user-language relationships
        ↓
COMMIT
        ↓
Profile completion recalculated
```

---

# 9. English-Only MVP Behavior

Because MVP supports English practice:

```text
learning_language = English
```

should not require the user to choose from many unsupported options.

Frontend may show:

```text
Practice Language: English
```

as fixed/read-only.

Backend must still validate that the submitted learning language is currently supported.

---

# 10. Mother Tongue

Mother tongue should be selected from language reference data.

Current open question:

```text
Can a user have more than one native language?
```

This has not been fully finalized.

Recommended MVP simplification:

```text
one primary mother tongue
```

while keeping the schema capable of multiple `NATIVE` relations later if needed.

Do not make a permanent architecture assumption that humans can only have one native language.

---

# 11. Languages Spoken

Profile may allow users to state languages they already speak.

This is useful for:

```text
profile display
future multilingual matching
community context
```

For English-only MVP, these values are secondary to:

```text
mother tongue
English learning/practice level
```

Exact maximum count remains open.

---

# 12. Learning Language

MVP:

```text
English
```

Future:

```text
multiple supported learning languages
```

The data model should support:

```text
user_id
language_id
relationship_type = LEARNING
proficiency_level
```

without requiring a schema redesign.

---

# 13. Proficiency Selection

The user self-selects their current English level.

Flow:

```text
Profile setup
   ↓
Choose:
A1 / A2 / B1 / B2 / C1 / C2
   ↓
Backend validates allowed value
   ↓
Persist
```

Do not trust arbitrary client strings.

---

# 14. Proficiency Updates

User may update their level later.

Example:

```text
B1
 ↓
B2
```

This should be allowed through profile/language update workflow.

For MVP, level changes are user-controlled.

Future:

```text
feedback
AI assessment
progress analytics
```

may provide recommendations, but should not silently overwrite the user's level unless explicitly designed.

---

# 15. Profile Integration

The client-facing language workflow should remain part of profile setup/editing.

Recommended API direction:

```text
GET /api/v1/languages
PUT /api/v1/profiles/me/languages
```

or equivalent.

Language owns:

```text
reference validation
relationship rules
```

Profile owns:

```text
user-facing profile setup workflow
```

---

# 16. Get Supported Languages

Recommended endpoint:

```text
GET /api/v1/languages
```

MVP response may return only:

```json
{
  "items": [
    {
      "code": "en",
      "name": "English"
    }
  ]
}
```

Future languages can be enabled without changing the endpoint contract.

---

# 17. Update User Languages

Conceptual request:

```json
{
  "mother_tongue": "hi",
  "spoken_languages": ["hi", "en"],
  "learning_language": "en",
  "proficiency_level": "B1"
}
```

For MVP:

```text
learning_language must be en
```

The exact API schema can use IDs instead of codes depending on implementation.

---

# 18. Validation Rules

Backend validates:

```text
language exists
language is active
relationship type valid
proficiency valid
learning language supported
duplicate relationships avoided
```

Example invalid input:

```text
proficiency = B7
```

→ reject.

Example unsupported learning language:

```text
learning_language = fr
```

while French is inactive/not supported

→ reject for MVP.

---

# 19. Duplicate Relationships

Avoid duplicate rows such as:

```text
user 10
English
LEARNING
```

appearing multiple times.

Database/application rule:

```text
UNIQUE(user_id, language_id, relationship_type)
```

where appropriate.

---

# 20. Profile Completion Dependency

Language data is part of profile-complete evaluation.

Conceptually:

```text
profile complete?
   ↓
mother tongue present?
learning language present?
English proficiency present?
```

If required language data is missing:

```text
PROFILE_INCOMPLETE
```

for matching/pairing eligibility.

---

# 21. Matching Integration

Matching consumes language information through a contract.

Example:

```text
LanguageReader
```

Potential fields:

```text
user_id
mother tongue
learning language
proficiency
spoken languages
```

Matching must not directly query Language repositories.

---

# 22. MVP Matching Language Rule

Since everyone practices English in MVP:

```text
both users must be eligible for English practice
```

Matching can use proficiency when ranking if the matching policy says so.

Exact proficiency compatibility formula remains a Matching-domain decision.

Examples that might later be considered:

```text
similar level
slightly different level
mixed levels
```

Do not encode an unapproved formula here.

---

# 23. Pairing Integration

Before entering automatic pairing:

```text
user language setup valid?
        ↓
English learning/practice configured?
        ↓
proficiency configured?
```

If no:

```text
PAIRING_NOT_ALLOWED
PROFILE_INCOMPLETE
```

---

# 24. Call UI Integration

When two users are paired/calling, frontend may show:

```text
partner name
English proficiency
mother tongue
shared interests
```

Call domain should receive only the safe summary it needs.

---

# 25. Future Multilingual Expansion

Future flow:

```text
Admin/platform enables Spanish
        ↓
languages table:
es → active
        ↓
Profile UI shows Spanish
        ↓
User can select Spanish learning relation
        ↓
Matching considers Spanish compatibility
        ↓
Pairing uses language-specific waiting pool
```

This should not require a new User table or redesign of Profile.

---

# 26. Future Pairing Queues

MVP conceptual Redis queue:

```text
pairing:queue:english
```

Future:

```text
pairing:queue:english
pairing:queue:spanish
pairing:queue:french
```

This is why language identifiers should be canonical and stable.

---

# 27. Language Deactivation

Future admin/system operation may mark a language inactive.

If a language becomes inactive:

```text
existing historical/profile data may remain
new selection should be prevented
new matching/pairing should not use it
```

Do not automatically delete user-language history merely because a language is temporarily unavailable.

---

# 28. Language Error Codes

Recommended:

```text
LANGUAGE_NOT_FOUND
LANGUAGE_NOT_SUPPORTED
LANGUAGE_INACTIVE
INVALID_LANGUAGE_RELATIONSHIP
INVALID_PROFICIENCY
DUPLICATE_USER_LANGUAGE
LEARNING_LANGUAGE_REQUIRED
PROFICIENCY_REQUIRED
```

---

# 29. Transaction Boundary

User language update may affect several relationships.

Target:

```text
BEGIN
  remove/update obsolete relations
  create/update current relations
COMMIT
```

The user should not end with a partially updated language profile.

---

# 30. Language API Security

All user-specific language changes require:

```text
authenticated user
```

Normal user:

```text
may update own language profile
```

Normal user must not:

```text
update another user's language profile
activate/deactivate platform languages
```

Platform language administration, if introduced, belongs to Admin.

---

# 31. Language Privacy

Language/profile information is generally part of the authenticated learner profile.

Visible examples:

```text
mother tongue
languages spoken
English proficiency
```

Private authentication fields remain unrelated and excluded.

---

# 32. Testing Workflow

## Reference Data

- English exists
- supported-language endpoint works
- inactive language rejected for new learning selection

## Proficiency

- A1 accepted
- A2 accepted
- B1 accepted
- B2 accepted
- C1 accepted
- C2 accepted
- invalid level rejected

## User Relations

- set mother tongue
- set English learning language
- duplicate relation prevented
- update proficiency
- user cannot modify another user's language data

## Profile Integration

- missing language data → profile incomplete
- complete valid language setup → profile eligible

## Matching/Pairing Integration

- eligible English learner can proceed
- unsupported/incomplete language configuration cannot enter pairing

---

# 33. Definition of Done — Language

Language workflow is ready when:

- [ ] English exists as active platform language.
- [ ] Supported-language endpoint works.
- [ ] User can set mother tongue.
- [ ] User can configure English as learning/practice language.
- [ ] User can select A1–C2 proficiency.
- [ ] Invalid proficiency is rejected.
- [ ] Unsupported learning languages are rejected in MVP.
- [ ] Duplicate user-language relations are prevented.
- [ ] User can update own language information.
- [ ] User cannot modify another user's language information.
- [ ] Profile completion uses required language information.
- [ ] Matching can consume language data through a contract.
- [ ] Pairing can validate English-practice eligibility.
- [ ] Tests pass.
- [ ] Schema remains extensible to future languages.

---

# 34. Language Workflow Diagram

```text
                   AUTHENTICATED USER
                          │
                          ▼
                    PROFILE SETUP
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
        MOTHER TONGUE   SPOKEN     LEARNING
                        LANGUAGES   LANGUAGE
                                      │
                                      ▼
                                   ENGLISH
                                      │
                                      ▼
                              SELECT CEFR LEVEL
                           A1 A2 B1 B2 C1 C2
                                      │
                                      ▼
                                  VALIDATE
                                      │
                                      ▼
                                   PERSIST
                                      │
                                      ▼
                           PROFILE ELIGIBILITY
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                     MATCHING                  PAIRING
```

---

# 35. Next Workflow

```text
AUTHENTICATION_WORKFLOW.md      ✅
PROFILE_WORKFLOW.md             ✅
LANGUAGE_WORKFLOW.md            ✅
        ↓
MATCHING_WORKFLOW.md            ← NEXT
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
