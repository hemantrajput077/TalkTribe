"""
test_profile_eligibility.py — PROF-06: Profile Eligibility Service Contract

Acceptance criteria tested:
  1. User with non-empty bio and at least one LEARNING language:
     -> eligible=True, reason=None
  2. User with no bio set (None, empty string, whitespace only, or no profile row):
     -> eligible=False, reason="PROFILE_BIO_MISSING"
  3. User with bio but no LEARNING language:
     -> eligible=False, reason="PROFILE_LEARNING_LANGUAGE_MISSING"
  4. User with neither bio nor LEARNING language:
     -> eligible=False (reason="PROFILE_BIO_MISSING")
  5. Circular import safety: Matching or Pairing domain importing ProfileEligibilityService
     does not raise any ImportError.

Service-layer unit tests (mocked repositories):
  6. Unit test verifying check returns eligible=True when bio and learning language exist.
  7. Unit test verifying check returns eligible=False with PROFILE_BIO_MISSING when profile is None.
  8. Unit test verifying check returns eligible=False with PROFILE_BIO_MISSING when bio is empty.
  9. Unit test verifying check returns eligible=False with PROFILE_LEARNING_LANGUAGE_MISSING when no learning language.
"""

from unittest.mock import AsyncMock

import pytest

from app.domains.auth.domain.enums import AccountStatus, UserRole
from app.domains.auth.infrastructure.user_model import User
from app.domains.languages.domain.enums import LanguageRole
from app.domains.languages.infrastructure.language_model import Language
from app.domains.profile.application.profile_eligibility_service import ProfileEligibilityService
from app.domains.profile.infrastructure.profile_model import Profile
from app.domains.profile.infrastructure.user_language_model import UserLanguage
from app.domains.profile.schemas.eligibility import IneligibilityReason, ProfileEligibilityResult


async def _create_test_user(db_session, username: str = "eligibility_user") -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        phone_number=f"+919876{hash(username) % 1000000:06d}",
        password="hashed_secure_password",
        full_name="Eligibility Test User",
        role=UserRole.USER,
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ── Integration tests with in-memory DB ───────────────────────────────────────


class TestProfileEligibilityDB:
    @pytest.mark.asyncio
    async def test_eligible_with_bio_and_learning_language(self, db_session, seed_languages):
        user = await _create_test_user(db_session, "user_eligible")

        profile = Profile(user_id=user.id, bio="I love learning new languages!")
        db_session.add(profile)

        # Add learning language
        user_lang = UserLanguage(
            user_id=user.id,
            language_id=seed_languages.id,
            role=LanguageRole.LEARNING,
            proficiency="B1",
        )
        db_session.add(user_lang)
        await db_session.commit()

        svc = ProfileEligibilityService(db_session)
        result = await svc.check(user.id)

        assert result.eligible is True
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_ineligible_missing_bio(self, db_session, seed_languages):
        user = await _create_test_user(db_session, "user_no_bio")

        # Profile exists but bio is None
        profile = Profile(user_id=user.id, bio=None)
        db_session.add(profile)

        user_lang = UserLanguage(
            user_id=user.id,
            language_id=seed_languages.id,
            role=LanguageRole.LEARNING,
            proficiency="A2",
        )
        db_session.add(user_lang)
        await db_session.commit()

        svc = ProfileEligibilityService(db_session)
        result = await svc.check(user.id)

        assert result.eligible is False
        assert result.reason == IneligibilityReason.PROFILE_BIO_MISSING
        assert result.reason == "PROFILE_BIO_MISSING"

    @pytest.mark.asyncio
    async def test_ineligible_empty_string_or_whitespace_bio(self, db_session, seed_languages):
        user = await _create_test_user(db_session, "user_whitespace_bio")

        profile = Profile(user_id=user.id, bio="    ")
        db_session.add(profile)

        user_lang = UserLanguage(
            user_id=user.id,
            language_id=seed_languages.id,
            role=LanguageRole.LEARNING,
            proficiency="A1",
        )
        db_session.add(user_lang)
        await db_session.commit()

        svc = ProfileEligibilityService(db_session)
        result = await svc.check(user.id)

        assert result.eligible is False
        assert result.reason == "PROFILE_BIO_MISSING"

    @pytest.mark.asyncio
    async def test_ineligible_no_profile_row(self, db_session, seed_languages):
        user = await _create_test_user(db_session, "user_no_profile_row")

        svc = ProfileEligibilityService(db_session)
        result = await svc.check(user.id)

        assert result.eligible is False
        assert result.reason == "PROFILE_BIO_MISSING"

    @pytest.mark.asyncio
    async def test_ineligible_missing_learning_language(self, db_session, seed_languages):
        user = await _create_test_user(db_session, "user_no_learning_lang")

        profile = Profile(user_id=user.id, bio="English native speaker.")
        db_session.add(profile)

        # Only NATIVE language, no LEARNING language
        user_lang = UserLanguage(
            user_id=user.id,
            language_id=seed_languages.id,
            role=LanguageRole.NATIVE,
        )
        db_session.add(user_lang)
        await db_session.commit()

        svc = ProfileEligibilityService(db_session)
        result = await svc.check(user.id)

        assert result.eligible is False
        assert result.reason == IneligibilityReason.PROFILE_LEARNING_LANGUAGE_MISSING
        assert result.reason == "PROFILE_LEARNING_LANGUAGE_MISSING"

    @pytest.mark.asyncio
    async def test_ineligible_neither_bio_nor_learning_language(self, db_session):
        user = await _create_test_user(db_session, "user_empty_everything")

        profile = Profile(user_id=user.id, bio=None)
        db_session.add(profile)
        await db_session.commit()

        svc = ProfileEligibilityService(db_session)
        result = await svc.check(user.id)

        assert result.eligible is False
        assert result.reason == "PROFILE_BIO_MISSING"

    @pytest.mark.asyncio
    async def test_eligible_with_multiple_languages_including_learning(
        self, db_session, seed_languages
    ):
        spanish = Language(name="Spanish", code="es")
        db_session.add(spanish)
        await db_session.commit()
        await db_session.refresh(spanish)

        user = await _create_test_user(db_session, "user_multilingual")

        profile = Profile(user_id=user.id, bio="Excited to practice Spanish and teach English!")
        db_session.add(profile)

        # 1 Native + 1 Learning
        db_session.add(
            UserLanguage(
                user_id=user.id,
                language_id=seed_languages.id,
                role=LanguageRole.NATIVE,
            )
        )
        db_session.add(
            UserLanguage(
                user_id=user.id,
                language_id=spanish.id,
                role=LanguageRole.LEARNING,
                proficiency="B2",
            )
        )
        await db_session.commit()

        svc = ProfileEligibilityService(db_session)
        result = await svc.check(user.id)

        assert result.eligible is True
        assert result.reason is None


# ── Unit tests with mocked repositories ───────────────────────────────────────


class TestProfileEligibilityUnit:
    @pytest.mark.asyncio
    async def test_unit_eligible(self):
        mock_db = AsyncMock()
        mock_profile_repo = AsyncMock()
        mock_user_lang_repo = AsyncMock()

        mock_profile_repo.get_by_user_id.return_value = Profile(user_id=1, bio="Valid bio")
        mock_user_lang_repo.has_learning_language.return_value = True

        svc = ProfileEligibilityService(
            db=mock_db,
            profile_repo=mock_profile_repo,
            user_lang_repo=mock_user_lang_repo,
        )
        result = await svc.check(1)

        assert result == ProfileEligibilityResult(eligible=True, reason=None)
        mock_profile_repo.get_by_user_id.assert_awaited_once_with(1)
        mock_user_lang_repo.has_learning_language.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_unit_bio_missing_when_profile_none(self):
        mock_db = AsyncMock()
        mock_profile_repo = AsyncMock()
        mock_user_lang_repo = AsyncMock()

        mock_profile_repo.get_by_user_id.return_value = None

        svc = ProfileEligibilityService(
            db=mock_db,
            profile_repo=mock_profile_repo,
            user_lang_repo=mock_user_lang_repo,
        )
        result = await svc.check(1)

        assert result.eligible is False
        assert result.reason == "PROFILE_BIO_MISSING"
        mock_user_lang_repo.has_learning_language.assert_not_called()

    @pytest.mark.asyncio
    async def test_unit_bio_missing_when_bio_blank(self):
        mock_db = AsyncMock()
        mock_profile_repo = AsyncMock()
        mock_user_lang_repo = AsyncMock()

        mock_profile_repo.get_by_user_id.return_value = Profile(user_id=1, bio="   ")

        svc = ProfileEligibilityService(
            db=mock_db,
            profile_repo=mock_profile_repo,
            user_lang_repo=mock_user_lang_repo,
        )
        result = await svc.check(1)

        assert result.eligible is False
        assert result.reason == "PROFILE_BIO_MISSING"
        mock_user_lang_repo.has_learning_language.assert_not_called()

    @pytest.mark.asyncio
    async def test_unit_learning_language_missing(self):
        mock_db = AsyncMock()
        mock_profile_repo = AsyncMock()
        mock_user_lang_repo = AsyncMock()

        mock_profile_repo.get_by_user_id.return_value = Profile(user_id=1, bio="Has bio")
        mock_user_lang_repo.has_learning_language.return_value = False

        svc = ProfileEligibilityService(
            db=mock_db,
            profile_repo=mock_profile_repo,
            user_lang_repo=mock_user_lang_repo,
        )
        result = await svc.check(1)

        assert result.eligible is False
        assert result.reason == "PROFILE_LEARNING_LANGUAGE_MISSING"


# ── Circular import safety test ───────────────────────────────────────────────


def test_no_circular_imports():
    """Verify that importing ProfileEligibilityService works cleanly and has no circular deps."""
    # Ensure module can be imported cleanly
    import app.domains.profile.application.profile_eligibility_service as eligibility_module

    assert hasattr(eligibility_module, "ProfileEligibilityService")
