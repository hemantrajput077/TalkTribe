"""
Create the two M2 profile bug-fix tickets on JIRA.

  Ticket 1 — PROF-BUG-01 (Critical, fix before M3)
    Covers BUG-01, BUG-03, BUG-04, BUG-05 from docs/bugs.md

  Ticket 2 — PROF-BUG-02 (High, parallel with early M3)
    Covers BUG-02 and BUG-06 (custom interests story)

Source:  docs/planning/epic-02-bug-fixes.md
Run:     python create_m2_bug_fixes.py
"""

from jira_client import JiraClient

# ── Ticket definitions ────────────────────────────────────────────────────────

TICKET_1 = {
    "bug_id": "PROF-BUG-01",
    "summary": "Fix critical M2 profile bugs blocking M3 (wrong query field, data loss on PATCH, missing validation, broken peer schema)",
    "priority": "critical",
    "labels": ["backend", "profile", "bug", "m2-stabilisation", "mvp"],
    "description": """\
Covers BUG-01, BUG-03, BUG-04, BUG-05. See docs/planning/epic-02-bug-fixes.md for full detail.
Must be merged before any M3 branch is created.

BUG-01 — GET /profiles/{user_id} returns the wrong user's profile.
ProfileRepository.get_safe_profile filters by Profile.id (auto-increment PK) instead of Profile.user_id.
Fix: change WHERE clause to Profile.user_id == user_id.
File: backend/app/domains/profile/infrastructure/profile_repository.py line 42.

BUG-03 — PATCH /profiles/me clears fields not included in the request (data loss).
update_profile overwrites every field including ones that default to None when not sent.
A user who sends {"location": "Mumbai"} loses their existing bio and profession.
Fix: use model_dump(exclude_unset=True) and setattr only for sent fields.
File: backend/app/domains/profile/infrastructure/profile_repository.py line 29.

BUG-04 — ProfileUpdate schema accepts oversized field values, no 422 returned.
bio max 500 chars, profession max 100 chars, location max 100 chars are all unvalidated.
Fix: add Field(max_length=...) constraints to ProfileUpdate and add extra="forbid".
File: backend/app/domains/profile/schemas/profile.py.

BUG-05 — UserProfileResponse inherits the write schema and is missing user_id.
Extends ProfileUpdate (an input schema) and exposes internal PK id instead of user_id.
M3 Matching cannot identify whose profile it received without user_id.
Fix: replace with a standalone PeerProfileResponse(user_id, bio, profession, location, avatar_url).
File: backend/app/domains/profile/schemas/profile.py line 27.

Acceptance Criteria:
- GET /profiles/5 returns the profile for user_id=5, not for profile row id=5.
- PATCH /profiles/me with only location does not clear existing bio or profession.
- PATCH /profiles/me with bio over 500 chars returns HTTP 422.
- PATCH /profiles/me with profession over 100 chars returns HTTP 422.
- GET /profiles/{user_id} response contains user_id field, not internal id.
- Existing profile test suite passes after all fixes.

Database Impact: None. No migrations required. All fixes are application-layer only.
""",
}

TICKET_2 = {
    "bug_id": "PROF-BUG-02",
    "summary": "Fix peer profile account-status check and implement custom interests (parallel M3 track)",
    "priority": "high",
    "labels": ["backend", "profile", "bug", "parallel-m3", "mvp"],
    "description": """\
Covers BUG-02 (bug) and BUG-06 / PROF-04 custom interests (story). Two separate PRs.
Must be merged before M3 Matching or Pairing is marked complete. Does not block M3 from starting.
See docs/planning/epic-02-bug-fixes.md for full detail.

--- Part A: BUG-02 — Peer profile does not check account status ---

GET /api/v1/profiles/{user_id} returns HTTP 200 for SUSPENDED, BLOCKED, and DELETED accounts.
Only the profiles table is queried — users.account_status is never checked.
Fix: add a JOIN to users table filtering WHERE account_status = ACTIVE.
Return 404 (not 403) for inactive accounts — do not reveal account state to callers.
Files: profile_repository.py get_safe_profile, profile_service.py get_safe_profile.

Acceptance Criteria Part A:
- ACTIVE account returns 200 with profile.
- SUSPENDED account returns 404.
- DELETED account returns 404.
- BLOCKED account returns 404.
- 404 response body does not contain the words suspended, blocked, or deleted.

Database Impact: None. Read-only JOIN on existing tables.

--- Part B: BUG-06 / PROF-04 — Custom interests not implemented (M2 exit criterion unmet) ---

Roadmap M2 exit criterion states "Custom interests work". Users cannot currently submit
interest names that are not in the predefined catalogue. InterestService rejects any
ID not in the seeded list — there is no path for free-text interest submission.
The interests table is also missing columns required by the database architecture design.

In Scope:
- Extend PUT /api/v1/profiles/me/interests to accept custom_interests: list[str]
- Trim, normalise (lowercase for dedup), store with display casing
- Reject: empty after trim, over 50 chars, exact normalised duplicate of existing interest
- Store custom interests with is_predefined=False and created_by_user_id set from identity
- GET /api/v1/interests returns only predefined interests (is_predefined=True)
- Combined interest_ids + custom_interests count must not exceed 10
- Migration to add is_predefined, created_by_user_id, is_active, created_at to interests table
- Backfill existing seeded rows with is_predefined=TRUE

Acceptance Criteria Part B:
- Valid custom interest is saved with is_predefined=False and returned in response.
- Duplicate custom interest name (case-insensitive) reuses existing row, no duplicate created.
- Empty or whitespace-only custom interest returns 422.
- Custom interest name over 50 chars returns 422.
- Combined count over 10 returns 422.
- GET /api/v1/interests returns only predefined interests, not custom ones.
- PUT replaces all previous selections including previously saved custom interests.
- Unauthenticated update returns 401.

Database Impact: Migration required on interests table (is_predefined, created_by_user_id, is_active, created_at).
""",
}


# ── Runner ─────────────────────────────────────────────────────────────────────

def main():
    client = JiraClient()

    # Verify connection first
    me = client.get_myself()
    print(f"\nConnected as: {me.get('displayName')} ({me.get('emailAddress')})")
    print(f"Project: {client.get_project().get('name')}\n")
    print("=" * 60)
    print("  Creating M2 Profile Bug Fix Tickets")
    print("=" * 60)

    results = []

    for ticket in [TICKET_1, TICKET_2]:
        result = client.create_bug(
            bug_id=ticket["bug_id"],
            summary=ticket["summary"],
            priority=ticket["priority"],
            labels=ticket["labels"],
            description=ticket["description"],
        )
        results.append({
            "bug_id": ticket["bug_id"],
            "key": result["key"],
            "summary": ticket["summary"],
        })

    print("\n" + "=" * 60)
    print("  DONE")
    print("=" * 60)
    for r in results:
        jira_base = client.base_url.replace("/rest/api/3", "")
        print(f"\n  {r['key']}  [{r['bug_id']}]")
        print(f"  {r['summary'][:70]}...")
        print(f"  {jira_base}/browse/{r['key']}")


if __name__ == "__main__":
    main()
