"""
test_matching.py — M3: Matching Epic

Acceptance criteria tested:

  Scoring engine (pure-unit, no DB):
    1.  Interest score: requester with 3 interests, candidate shares 3 → 60 pts.
    2.  Interest score: requester with 3 interests, candidate shares 1 → 20 pts.
    3.  Interest score: no shared interests → 0 pts.
    4.  Interest score: requester has no interests → 0 pts.
    5.  Profession score: identical (case-insensitive) → 20 pts.
    6.  Profession score: different → 0 pts.
    7.  Profession score: requester has no profession → 0 pts, candidate not excluded.
    8.  Profession score: candidate has no profession → 0 pts, candidate not excluded.
    9.  Proficiency score: same level (B1/B1) → 20 pts.
    10. Proficiency score: one apart (A1/A2) → 16 pts.
    11. Proficiency score: max distance (A1/C2) → 0 pts.
    12. Proficiency score: unknown level → 0 pts (graceful degradation).
    13. score_candidate: returns sum of three components, bounded 0–100.

  InteractionEligibility stub (pure-unit):
    14. NullInteractionEligibility always returns True regardless of IDs.

  API / integration tests (in-memory SQLite + HTTP client):
    15. Unauthenticated request → 401.
    16. Authenticated but incomplete profile (no bio) → 403 PROFILE_BIO_MISSING.
    17. Authenticated but no learning language → 403 PROFILE_LEARNING_LANGUAGE_MISSING.
    18. Eligible requester, no other users → 200 with empty items list.
    19. Self excluded from results.
    20. Inactive candidate (is_active=False) excluded.
    21. Non-ACTIVE account status candidate excluded.
    22. Candidate with incomplete profile (no bio) excluded.
    23. More shared interests → higher rank (interest is primary signal).
    24. Same score → stable tie-break by ascending user_id.
    25. Profession match raises rank when interests are equal.
    26. Results never exceed 20 even if more candidates exist.
    27. Server enforces cap — client cannot bypass with limit param > 20.
    28. Response shape: items list, count, all required fields present.
    29. Safe fields only — no email, phone, password in response.
    30. Deterministic: identical state produces identical result.
"""

from unittest.mock import AsyncMock

import pytest

from app.domains.auth.domain.enums import AccountStatus, UserRole
from app.domains.auth.infrastructure.user_model import User
from app.domains.languages.domain.enums import LanguageRole
from app.domains.languages.infrastructure.language_model import Language
from app.domains.matching.application.profile_matching_reader import CandidateSummary
from app.domains.matching.application.scoring_engine import (
    _interest_score,
    _profession_score,
    _proficiency_score,
    score_candidate,
)
from app.domains.matching.contracts.interaction_eligibility import NullInteractionEligibility
from app.domains.profile.infrastructure.profile_model import Profile
from app.domains.profile.infrastructure.user_language_model import UserLanguage

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
LOGIN_URL = "/api/v1/auth/login"
MATCHES_URL = "/api/v1/matches"


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _register_verify_login(client, mock_send_email, user: dict) -> str:
    """Register → verify email → login. Returns the access token."""
    await client.post(REGISTER_URL, json=user)
    otp = mock_send_email.call_args[0][1]
    await client.post(VERIFY_URL, json={"email": user["email"], "otp": otp})
    resp = await client.post(
        LOGIN_URL,
        json={"username": user["username"], "password": user["password"]},
    )
    return resp.json()["access_token"]


async def _make_eligible(db_session, user_id: int, language_id: int, bio: str = "Hi!") -> None:
    """Give a user a bio + LEARNING language so ProfileEligibilityService passes."""
    profile = Profile(user_id=user_id, bio=bio)
    db_session.add(profile)
    db_session.add(
        UserLanguage(
            user_id=user_id,
            language_id=language_id,
            role=LanguageRole.LEARNING,
            proficiency="B1",
        )
    )
    await db_session.commit()


async def _create_user_direct(
    db_session,
    username: str,
    account_status: AccountStatus = AccountStatus.ACTIVE,
    is_active: bool = True,
) -> User:
    """Directly insert an ACTIVE user without going through the HTTP API."""
    user = User(
        username=username,
        email=f"{username}@example.com",
        phone_number=f"+91{abs(hash(username)) % 10000000000:010d}",
        password="hashed_password",
        full_name=username.capitalize(),
        role=UserRole.USER,
        account_status=account_status,
        is_active=is_active,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ── Pure-unit: scoring engine ─────────────────────────────────────────────────


class TestInterestScore:
    """Tests 1–4: _interest_score"""

    def test_full_overlap(self):
        """Test 1: all requester interests shared → 60 pts."""
        assert _interest_score({1, 2, 3}, {1, 2, 3}) == 60

    def test_partial_overlap(self):
        """Test 2: 1 of 3 shared → 20 pts (round(1/3 * 60))."""
        assert _interest_score({1, 2, 3}, {1, 10, 11}) == 20

    def test_no_overlap(self):
        """Test 3: zero shared → 0 pts."""
        assert _interest_score({1, 2, 3}, {4, 5, 6}) == 0

    def test_requester_has_no_interests(self):
        """Test 4: requester has no interests → 0 pts (no division by zero)."""
        assert _interest_score(set(), {1, 2, 3}) == 0


class TestProfessionScore:
    """Tests 5–8: _profession_score"""

    def test_same_profession(self):
        """Test 5: identical profession → 20 pts."""
        assert _profession_score("Software Engineer", "Software Engineer") == 20

    def test_same_profession_case_insensitive(self):
        """Test 5 (case): case-insensitive match → 20 pts."""
        assert _profession_score("developer", "Developer") == 20

    def test_different_profession(self):
        """Test 6: different → 0 pts."""
        assert _profession_score("Designer", "Engineer") == 0

    def test_requester_no_profession(self):
        """Test 7: requester None → 0 pts (never ineligible)."""
        assert _profession_score(None, "Engineer") == 0

    def test_candidate_no_profession(self):
        """Test 8: candidate None → 0 pts (never ineligible)."""
        assert _profession_score("Engineer", None) == 0


class TestProficiencyScore:
    """Tests 9–12: _proficiency_score"""

    def test_same_level(self):
        """Test 9: B1 / B1 → 20 pts (distance=0)."""
        assert _proficiency_score("B1", "B1") == 20

    def test_adjacent_level(self):
        """Test 10: A1 / A2 → distance=1 → 20 - 4 = 16 pts."""
        assert _proficiency_score("A1", "A2") == 16

    def test_max_distance(self):
        """Test 11: A1 / C2 → distance=5 → 0 pts."""
        assert _proficiency_score("A1", "C2") == 0

    def test_unknown_level(self):
        """Test 12: unrecognised level → 0 pts (graceful degradation)."""
        assert _proficiency_score("X9", "B1") == 0
        assert _proficiency_score("B1", None) == 0
        assert _proficiency_score(None, None) == 0


class TestScoreCandidate:
    """Test 13: score_candidate aggregates components."""

    def test_aggregate_score(self):
        """Score is sum of three components, bounded 0–100."""
        candidate = CandidateSummary(
            user_id=99,
            display_name="Candidate",
            avatar_url=None,
            profession="Developer",
            proficiency_level="B1",
            interest_ids={1, 2, 3},
        )
        # interest: 3/3 * 60 = 60
        # profession: same = 20
        # proficiency: same level = 20
        # total = 100
        total = score_candidate(
            requester_interest_ids={1, 2, 3},
            requester_profession="developer",
            requester_proficiency="B1",
            candidate=candidate,
        )
        assert total == 100

    def test_no_shared_signals(self):
        """Score is 0 when nothing matches and profession/proficiency are missing."""
        candidate = CandidateSummary(
            user_id=99,
            display_name="Candidate",
            avatar_url=None,
            profession=None,
            proficiency_level=None,
            interest_ids={10, 11, 12},
        )
        total = score_candidate(
            requester_interest_ids={1, 2, 3},
            requester_profession=None,
            requester_proficiency=None,
            candidate=candidate,
        )
        assert total == 0


# ── Pure-unit: interaction eligibility stub ───────────────────────────────────


class TestNullInteractionEligibility:
    """Test 14: NullInteractionEligibility."""

    @pytest.mark.asyncio
    async def test_always_eligible(self):
        stub = NullInteractionEligibility()
        assert await stub.are_interaction_eligible(1, 2) is True
        assert await stub.are_interaction_eligible(99, 1) is True
        assert await stub.are_interaction_eligible(0, 0) is True


# ── Integration tests ─────────────────────────────────────────────────────────

_REQUESTER = {
    "username": "requester",
    "email": "requester@example.com",
    "phone_number": "+919000000001",
    "password": "SecurePass1!",
    "full_name": "Requester User",
}


class TestMatchesAPI:
    """Tests 15–30: GET /api/v1/matches"""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, client, mock_send_email):
        """Test 15."""
        resp = await client.get(MATCHES_URL)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_no_bio_returns_403(self, client, mock_send_email, seed_languages):
        """Test 16: eligible account but profile has no bio → 403."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)
        # No profile created at all (or no bio) → ProfileEligibilityService rejects
        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "PROFILE_BIO_MISSING"

    @pytest.mark.asyncio
    async def test_no_learning_language_returns_403(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 17: bio present but no LEARNING language → 403."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()

        profile = Profile(user_id=requester_id, bio="I love English!")
        db_session.add(profile)
        await db_session.commit()

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "PROFILE_LEARNING_LANGUAGE_MISSING"

    @pytest.mark.asyncio
    async def test_empty_results_when_no_other_users(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 18: eligible requester, no other users → 200 empty list."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["count"] == 0

    @pytest.mark.asyncio
    async def test_self_excluded(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 19: the requester's own user_id must not appear in results."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        returned_ids = [item["user_id"] for item in resp.json()["items"]]
        assert requester_id not in returned_ids

    @pytest.mark.asyncio
    async def test_inactive_is_active_false_excluded(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 20: candidate with is_active=False is excluded."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        # Candidate with is_active=False
        candidate = await _create_user_direct(db_session, "inactive_candidate", is_active=False)
        await _make_eligible(db_session, candidate.id, seed_languages.id)

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        returned_ids = [item["user_id"] for item in resp.json()["items"]]
        assert candidate.id not in returned_ids

    @pytest.mark.asyncio
    async def test_non_active_account_status_excluded(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 21: candidate with account_status SUSPENDED is excluded."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        candidate = await _create_user_direct(
            db_session, "suspended_candidate", account_status=AccountStatus.SUSPENDED
        )
        await _make_eligible(db_session, candidate.id, seed_languages.id)

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        returned_ids = [item["user_id"] for item in resp.json()["items"]]
        assert candidate.id not in returned_ids

    @pytest.mark.asyncio
    async def test_candidate_with_no_bio_excluded(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 22: candidate without bio is excluded even if ACTIVE."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        incomplete = await _create_user_direct(db_session, "no_bio_candidate")
        # Give learning language but NO bio
        db_session.add(
            UserLanguage(
                user_id=incomplete.id,
                language_id=seed_languages.id,
                role=LanguageRole.LEARNING,
                proficiency="A2",
            )
        )
        await db_session.commit()

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        returned_ids = [item["user_id"] for item in resp.json()["items"]]
        assert incomplete.id not in returned_ids

    @pytest.mark.asyncio
    async def test_more_shared_interests_ranks_higher(
        self, client, mock_send_email, db_session, seed_languages, seed_interests
    ):
        """Test 23: candidate with more shared interests appears first."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User
        from app.domains.profile.infrastructure.user_interest_model import UserInterest

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        # Requester: interests 1, 2, 3
        for iid in [1, 2, 3]:
            db_session.add(UserInterest(user_id=requester_id, interest_id=iid))
        await db_session.commit()

        # Candidate A: shares 2 (interests 1, 2)
        cand_a = await _create_user_direct(db_session, "cand_a_two_shared")
        await _make_eligible(db_session, cand_a.id, seed_languages.id)
        for iid in [1, 2]:
            db_session.add(UserInterest(user_id=cand_a.id, interest_id=iid))
        await db_session.commit()

        # Candidate B: shares 1 (interest 1 only)
        cand_b = await _create_user_direct(db_session, "cand_b_one_shared")
        await _make_eligible(db_session, cand_b.id, seed_languages.id)
        db_session.add(UserInterest(user_id=cand_b.id, interest_id=1))
        await db_session.commit()

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        ids = [item["user_id"] for item in resp.json()["items"]]
        assert ids.index(cand_a.id) < ids.index(cand_b.id), (
            "Candidate A (2 shared interests) must rank above Candidate B (1 shared interest)"
        )

    @pytest.mark.asyncio
    async def test_tie_break_by_user_id_ascending(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 24: equal score → lower user_id appears first."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        # Two candidates with identical profiles → same score
        cand_x = await _create_user_direct(db_session, "tie_cand_x")
        await _make_eligible(db_session, cand_x.id, seed_languages.id)

        cand_y = await _create_user_direct(db_session, "tie_cand_y")
        await _make_eligible(db_session, cand_y.id, seed_languages.id)

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        ids = [item["user_id"] for item in resp.json()["items"]]
        # Both must appear; lower user_id must come first
        assert cand_x.id in ids
        assert cand_y.id in ids
        if cand_x.id < cand_y.id:
            assert ids.index(cand_x.id) < ids.index(cand_y.id)
        else:
            assert ids.index(cand_y.id) < ids.index(cand_x.id)

    @pytest.mark.asyncio
    async def test_profession_match_raises_rank(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 25: equal interests but same profession → higher rank."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()

        # Give requester a profession
        profile = Profile(user_id=requester_id, bio="Hi!", profession="Engineer")
        db_session.add(profile)
        db_session.add(
            UserLanguage(
                user_id=requester_id,
                language_id=seed_languages.id,
                role=LanguageRole.LEARNING,
                proficiency="B1",
            )
        )
        await db_session.commit()

        # Candidate with same profession (no shared interests)
        cand_same_prof = await _create_user_direct(db_session, "same_prof_cand")
        profile_s = Profile(user_id=cand_same_prof.id, bio="Hi!", profession="Engineer")
        db_session.add(profile_s)
        db_session.add(
            UserLanguage(
                user_id=cand_same_prof.id,
                language_id=seed_languages.id,
                role=LanguageRole.LEARNING,
                proficiency="B1",
            )
        )
        await db_session.commit()

        # Candidate with different profession (no shared interests)
        cand_diff_prof = await _create_user_direct(db_session, "diff_prof_cand")
        profile_d = Profile(user_id=cand_diff_prof.id, bio="Hi!", profession="Designer")
        db_session.add(profile_d)
        db_session.add(
            UserLanguage(
                user_id=cand_diff_prof.id,
                language_id=seed_languages.id,
                role=LanguageRole.LEARNING,
                proficiency="B1",
            )
        )
        await db_session.commit()

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        ids = [item["user_id"] for item in resp.json()["items"]]
        scores = {item["user_id"]: item["compatibility_score"] for item in resp.json()["items"]}
        assert scores[cand_same_prof.id] > scores[cand_diff_prof.id], (
            "Same profession must score higher than different profession"
        )

    @pytest.mark.asyncio
    async def test_results_capped_at_20(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 26: at most 20 results returned even with 25 eligible candidates."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        # Create 25 eligible candidates
        for i in range(25):
            cand = await _create_user_direct(db_session, f"cap_cand_{i:02d}")
            await _make_eligible(db_session, cand.id, seed_languages.id)

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) <= 20
        assert body["count"] <= 20

    @pytest.mark.asyncio
    async def test_client_cannot_bypass_cap_with_limit(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 27: passing limit > 20 in query is rejected by schema (422) or capped."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        # limit=1000 must be rejected at validation layer (le=20 constraint)
        resp = await client.get(
            MATCHES_URL + "?limit=1000",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_response_shape_correct(
        self, client, mock_send_email, db_session, seed_languages, seed_interests
    ):
        """Test 28: response has items list and count field; each item has required fields."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User
        from app.domains.profile.infrastructure.user_interest_model import UserInterest

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)
        db_session.add(UserInterest(user_id=requester_id, interest_id=1))
        await db_session.commit()

        cand = await _create_user_direct(db_session, "shape_cand")
        await _make_eligible(db_session, cand.id, seed_languages.id)
        db_session.add(UserInterest(user_id=cand.id, interest_id=1))
        await db_session.commit()

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "count" in body
        assert body["count"] == len(body["items"])

        for item in body["items"]:
            assert "user_id" in item
            assert "display_name" in item
            assert "profile_photo_url" in item
            assert "proficiency_level" in item
            assert "shared_interests" in item
            assert "profession" in item
            assert "compatibility_score" in item

    @pytest.mark.asyncio
    async def test_safe_fields_only_no_sensitive_data(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 29: email, phone, password, etc. must not appear in match response."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        cand = await _create_user_direct(db_session, "safe_field_cand")
        await _make_eligible(db_session, cand.id, seed_languages.id)

        resp = await client.get(
            MATCHES_URL, headers={"Authorization": f"Bearer {token}"}
        )
        raw_text = resp.text.lower()
        # Ensure none of the sensitive fields leak
        assert "password" not in raw_text
        assert "phone_number" not in raw_text
        # Email may appear in the response if display_name is an email, so check field names
        body = resp.json()
        for item in body["items"]:
            assert "email" not in item
            assert "phone" not in item
            assert "password" not in item
            assert "otp" not in item
            assert "refresh_token" not in item

    @pytest.mark.asyncio
    async def test_deterministic_same_state_same_result(
        self, client, mock_send_email, db_session, seed_languages
    ):
        """Test 30: two calls with identical state return identical results."""
        token = await _register_verify_login(client, mock_send_email, _REQUESTER)

        from sqlalchemy import select
        from app.domains.auth.infrastructure.user_model import User

        result = await db_session.execute(
            select(User.id).where(User.username == _REQUESTER["username"])
        )
        requester_id = result.scalar_one()
        await _make_eligible(db_session, requester_id, seed_languages.id)

        cand = await _create_user_direct(db_session, "deterministic_cand")
        await _make_eligible(db_session, cand.id, seed_languages.id)

        headers = {"Authorization": f"Bearer {token}"}
        resp1 = await client.get(MATCHES_URL, headers=headers)
        resp2 = await client.get(MATCHES_URL, headers=headers)

        assert resp1.json() == resp2.json()
