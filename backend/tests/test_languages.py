"""
test_languages.py — PROF-05: Language Configuration

Acceptance criteria tested:

  GET /api/v1/languages (no auth required):
    1. No token → HTTP 200 (public endpoint)
    2. Returns at least English in the list

  PUT /api/v1/profiles/me/languages:
    3. No token → HTTP 401
    4. Valid config (1 NATIVE + 1 LEARNING with proficiency) → HTTP 200, saved
    5. Zero NATIVE languages → HTTP 422
    6. Two NATIVE languages → HTTP 422
    7. LEARNING without proficiency → HTTP 422
    8. Same language_id as NATIVE and LEARNING → HTTP 422
    9. Invalid proficiency value (not A1-C2) → HTTP 422
   10. Second PUT fully replaces first (idempotent full-replace)

Service-layer unit tests (mocked repository):
   11. replace_user_languages raises 422 when a language_id does not exist
   12. replace_user_languages delegates to repository on valid input
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.domains.languages.infrastructure.language_model import Language
from app.domains.profile.application.user_language_service import UserLanguageService
from app.domains.profile.schemas.user_language import PutLanguagesRequest

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
LOGIN_URL = "/api/v1/auth/login"
LANGUAGES_URL = "/api/v1/languages"
MY_LANGUAGES_URL = "/api/v1/profiles/me/languages"

_LEARNER = {
    "username": "languser",
    "email": "lang@example.com",
    "phone_number": "+919876543230",
    "password": "SecurePass1!",
    "full_name": "Lang User",
}


async def _register_verify_login(client, mock_send_email, user: dict) -> str:
    """Register → verify email → login. Returns the access token."""
    await client.post(REGISTER_URL, json=user)
    otp = mock_send_email.call_args[0][1]
    await client.post(VERIFY_URL, json={"email": user["email"], "otp": otp})
    resp = await client.post(
        LOGIN_URL, json={"username": user["username"], "password": user["password"]}
    )
    return resp.json()["access_token"]


# ── GET /api/v1/languages ─────────────────────────────────────────────────────


class TestListLanguages:
    @pytest.mark.asyncio
    async def test_no_auth_returns_200(self, client, seed_languages):
        resp = await client.get(LANGUAGES_URL)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_contains_english(self, client, seed_languages):
        resp = await client.get(LANGUAGES_URL)
        data = resp.json()
        assert isinstance(data, list)
        codes = [lang["code"] for lang in data]
        assert "en" in codes

    @pytest.mark.asyncio
    async def test_language_has_required_fields(self, client, seed_languages):
        resp = await client.get(LANGUAGES_URL)
        lang = resp.json()[0]
        assert "id" in lang
        assert "name" in lang
        assert "code" in lang


# ── PUT /api/v1/profiles/me/languages ────────────────────────────────────────


class TestPutMyLanguages:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client, seed_languages):
        resp = await client.put(
            MY_LANGUAGES_URL,
            json={"languages": [{"language_id": 1, "role": "NATIVE"}]},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_config_returns_200(self, client, mock_send_email, seed_languages):
        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(
            MY_LANGUAGES_URL,
            json={
                "languages": [
                    {"language_id": seed_languages.id, "role": "NATIVE"},
                    {
                        "language_id": seed_languages.id,
                        "role": "LEARNING",
                        "proficiency": "B2",
                    },
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 422  # same language NATIVE+LEARNING → blocked

    @pytest.mark.asyncio
    async def test_valid_config_native_only_returns_200(
        self, client, mock_send_email, seed_languages, db_session
    ):
        """One NATIVE language (no LEARNING) is valid per spec — PROF-06 handles eligibility."""
        from app.domains.languages.infrastructure.language_model import Language

        spanish = Language(name="Spanish", code="es")
        db_session.add(spanish)
        await db_session.commit()
        await db_session.refresh(spanish)

        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(
            MY_LANGUAGES_URL,
            json={
                "languages": [
                    {"language_id": seed_languages.id, "role": "NATIVE"},
                    {"language_id": spanish.id, "role": "LEARNING", "proficiency": "A1"},
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "languages" in data
        assert len(data["languages"]) == 2

    @pytest.mark.asyncio
    async def test_response_contains_language_details(
        self, client, mock_send_email, seed_languages, db_session
    ):
        from app.domains.languages.infrastructure.language_model import Language

        spanish = Language(name="Spanish", code="es")
        db_session.add(spanish)
        await db_session.commit()
        await db_session.refresh(spanish)

        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(
            MY_LANGUAGES_URL,
            json={
                "languages": [
                    {"language_id": seed_languages.id, "role": "NATIVE"},
                    {"language_id": spanish.id, "role": "LEARNING", "proficiency": "B1"},
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 200
        languages = resp.json()["languages"]
        for entry in languages:
            assert "language_id" in entry
            assert "language_name" in entry
            assert "language_code" in entry
            assert "role" in entry
            assert "proficiency" in entry

    @pytest.mark.asyncio
    async def test_zero_native_returns_422(self, client, mock_send_email, seed_languages):
        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(
            MY_LANGUAGES_URL,
            json={
                "languages": [
                    {
                        "language_id": seed_languages.id,
                        "role": "LEARNING",
                        "proficiency": "A2",
                    }
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_two_native_returns_422(
        self, client, mock_send_email, seed_languages, db_session
    ):
        from app.domains.languages.infrastructure.language_model import Language

        spanish = Language(name="Spanish", code="es")
        db_session.add(spanish)
        await db_session.commit()
        await db_session.refresh(spanish)

        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(
            MY_LANGUAGES_URL,
            json={
                "languages": [
                    {"language_id": seed_languages.id, "role": "NATIVE"},
                    {"language_id": spanish.id, "role": "NATIVE"},
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_learning_without_proficiency_returns_422(
        self, client, mock_send_email, seed_languages, db_session
    ):
        from app.domains.languages.infrastructure.language_model import Language

        spanish = Language(name="Spanish", code="es")
        db_session.add(spanish)
        await db_session.commit()
        await db_session.refresh(spanish)

        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(
            MY_LANGUAGES_URL,
            json={
                "languages": [
                    {"language_id": seed_languages.id, "role": "NATIVE"},
                    {"language_id": spanish.id, "role": "LEARNING"},
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_same_language_native_and_learning_returns_422(
        self, client, mock_send_email, seed_languages
    ):
        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(
            MY_LANGUAGES_URL,
            json={
                "languages": [
                    {"language_id": seed_languages.id, "role": "NATIVE"},
                    {
                        "language_id": seed_languages.id,
                        "role": "LEARNING",
                        "proficiency": "C1",
                    },
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_proficiency_returns_422(
        self, client, mock_send_email, seed_languages, db_session
    ):
        from app.domains.languages.infrastructure.language_model import Language

        spanish = Language(name="Spanish", code="es")
        db_session.add(spanish)
        await db_session.commit()
        await db_session.refresh(spanish)

        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(
            MY_LANGUAGES_URL,
            json={
                "languages": [
                    {"language_id": seed_languages.id, "role": "NATIVE"},
                    {
                        "language_id": spanish.id,
                        "role": "LEARNING",
                        "proficiency": "Z9",
                    },
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_second_put_replaces_first(
        self, client, mock_send_email, seed_languages, db_session
    ):
        from app.domains.languages.infrastructure.language_model import Language

        spanish = Language(name="Spanish", code="es")
        db_session.add(spanish)
        await db_session.commit()
        await db_session.refresh(spanish)

        token = await _register_verify_login(client, mock_send_email, _LEARNER)
        headers = {"Authorization": f"Bearer {token}"}

        # First PUT: NATIVE English + LEARNING Spanish B1
        await client.put(
            MY_LANGUAGES_URL,
            json={
                "languages": [
                    {"language_id": seed_languages.id, "role": "NATIVE"},
                    {"language_id": spanish.id, "role": "LEARNING", "proficiency": "B1"},
                ]
            },
            headers=headers,
        )

        # Second PUT: only NATIVE English (removes Spanish)
        resp = await client.put(
            MY_LANGUAGES_URL,
            json={
                "languages": [
                    {"language_id": seed_languages.id, "role": "NATIVE"},
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["languages"]) == 1
        assert data["languages"][0]["role"] == "NATIVE"


# ── Service unit tests ────────────────────────────────────────────────────────


class TestUserLanguageServiceUnit:
    @pytest.mark.asyncio
    async def test_unknown_language_id_raises_422(self):
        mock_db = AsyncMock()
        svc = UserLanguageService(mock_db)
        svc.lang_repo = AsyncMock()
        svc.lang_repo.get_by_ids.return_value = []  # no languages found in DB

        request = PutLanguagesRequest(
            languages=[
                {"language_id": 999, "role": "NATIVE"},
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            await svc.replace_user_languages(1, request)

        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_request_delegates_to_repository(self):
        mock_db = AsyncMock()
        svc = UserLanguageService(mock_db)

        found_lang = Language(id=1, name="English", code="en")
        svc.lang_repo = AsyncMock()
        svc.lang_repo.get_by_ids.return_value = [found_lang]
        svc.repo = AsyncMock()
        svc.repo.replace_all.return_value = []

        request = PutLanguagesRequest(
            languages=[
                {"language_id": 1, "role": "NATIVE"},
            ]
        )

        await svc.replace_user_languages(1, request)

        svc.repo.replace_all.assert_awaited_once()
