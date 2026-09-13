"""
test_interests.py — GET /api/v1/interests  &  PUT /api/v1/profiles/me/interests  (TT-14)

Acceptance criteria tested:
  GET /interests
    1. No auth required — returns 200 with the full catalogue.
    2. Response contains exactly 14 interests.
    3. Each item has id and name fields.

  PUT /profiles/me/interests
    4. No token → 401.
    5. Valid list of ≤ 10 IDs → 200, returns saved interests.
    6. Replace semantics — subsequent PUT overwrites previous selections.
    7. Empty list → 200, clears all interests.
    8. 11 or more IDs → 422 (Pydantic max-10 validator).
    9. Non-existent interest ID → 422 (service validation).
    10. Response contains id and name for each saved interest.

Service-layer unit tests (mocked repository):
    11. set_user_interests raises 422 for an unknown ID.
    12. set_user_interests calls repo.replace_user_interests on success.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.domains.profile.application.interest_service import InterestService
from app.domains.profile.infrastructure.interest_model import Interest

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
LOGIN_URL = "/api/v1/auth/login"
INTERESTS_URL = "/api/v1/interests"
MY_INTERESTS_URL = "/api/v1/profiles/me/interests"

_USER = {
    "username": "interestuser",
    "email": "interest@example.com",
    "phone_number": "+919876543230",
    "password": "SecurePass1!",
    "full_name": "Interest User",
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


# ── GET /interests ─────────────────────────────────────────────────────────────


class TestListInterests:
    @pytest.mark.asyncio
    async def test_no_auth_returns_200(self, client, seed_interests):
        resp = await client.get(INTERESTS_URL)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_all_14_interests(self, client, seed_interests):
        resp = await client.get(INTERESTS_URL)
        data = resp.json()
        assert len(data["interests"]) == 14

    @pytest.mark.asyncio
    async def test_each_item_has_id_and_name(self, client, seed_interests):
        resp = await client.get(INTERESTS_URL)
        for item in resp.json()["interests"]:
            assert "id" in item
            assert "name" in item
            assert isinstance(item["id"], int)
            assert isinstance(item["name"], str)

    @pytest.mark.asyncio
    async def test_interests_sorted_alphabetically(self, client, seed_interests):
        resp = await client.get(INTERESTS_URL)
        names = [i["name"] for i in resp.json()["interests"]]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_contains_expected_names(self, client, seed_interests):
        resp = await client.get(INTERESTS_URL)
        names = {i["name"] for i in resp.json()["interests"]}
        expected = {
            "Music",
            "Travel",
            "Technology",
            "Sports",
            "Movies",
            "Books",
            "Cooking",
            "Gaming",
            "Art",
            "Science",
            "Business",
            "Fashion",
            "Nature",
            "Fitness",
        }
        assert names == expected


# ── PUT /profiles/me/interests ─────────────────────────────────────────────────


class TestSetMyInterests:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client, seed_interests):
        resp = await client.put(MY_INTERESTS_URL, json={"interest_ids": [1, 2]})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_selection_returns_200(self, client, mock_send_email, seed_interests):
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(MY_INTERESTS_URL, json={"interest_ids": [1, 2, 3]}, headers=headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_contains_id_and_name(self, client, mock_send_email, seed_interests):
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(MY_INTERESTS_URL, json={"interest_ids": [9, 13]}, headers=headers)
        data = resp.json()
        assert "interests" in data
        for item in data["interests"]:
            assert "id" in item
            assert "name" in item

    @pytest.mark.asyncio
    async def test_response_contains_saved_names(self, client, mock_send_email, seed_interests):
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(MY_INTERESTS_URL, json={"interest_ids": [9, 13]}, headers=headers)
        names = {i["name"] for i in resp.json()["interests"]}
        assert names == {"Music", "Technology"}

    @pytest.mark.asyncio
    async def test_replace_semantics(self, client, mock_send_email, seed_interests):
        """PUT with 3 IDs, then PUT with 2 different IDs — only the 2 new ones remain."""
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        await client.put(MY_INTERESTS_URL, json={"interest_ids": [1, 2, 3]}, headers=headers)
        resp = await client.put(MY_INTERESTS_URL, json={"interest_ids": [9, 14]}, headers=headers)
        names = {i["name"] for i in resp.json()["interests"]}
        assert names == {"Music", "Travel"}
        assert len(resp.json()["interests"]) == 2

    @pytest.mark.asyncio
    async def test_empty_list_clears_interests(self, client, mock_send_email, seed_interests):
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        await client.put(MY_INTERESTS_URL, json={"interest_ids": [1, 2]}, headers=headers)
        resp = await client.put(MY_INTERESTS_URL, json={"interest_ids": []}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["interests"] == []

    @pytest.mark.asyncio
    async def test_eleven_ids_returns_422(self, client, mock_send_email, seed_interests):
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        ids = list(range(1, 12))  # 11 unique IDs
        resp = await client.put(MY_INTERESTS_URL, json={"interest_ids": ids}, headers=headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_interest_id_returns_422(self, client, mock_send_email, seed_interests):
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(MY_INTERESTS_URL, json={"interest_ids": [9999]}, headers=headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_duplicates_are_deduplicated(self, client, mock_send_email, seed_interests):
        """Duplicate IDs count as one — [1,1,1] → 1 saved interest."""
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.put(MY_INTERESTS_URL, json={"interest_ids": [1, 1, 1]}, headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()["interests"]) == 1


# ── GET /profiles/me/interests ─────────────────────────────────────────────────


class TestGetMyInterests:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client, seed_interests):
        resp = await client.get(MY_INTERESTS_URL)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_interests_set(
        self, client, mock_send_email, seed_interests
    ):
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(MY_INTERESTS_URL, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["interests"] == []

    @pytest.mark.asyncio
    async def test_returns_saved_interests(self, client, mock_send_email, seed_interests):
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        # First set interests
        await client.put(MY_INTERESTS_URL, json={"interest_ids": [9, 13]}, headers=headers)

        # Then GET them back
        resp = await client.get(MY_INTERESTS_URL, headers=headers)
        assert resp.status_code == 200
        names = {i["name"] for i in resp.json()["interests"]}
        assert names == {"Music", "Technology"}

    @pytest.mark.asyncio
    async def test_get_reflects_latest_put(self, client, mock_send_email, seed_interests):
        """After replacing interests with PUT, GET should return the new list."""
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        await client.put(MY_INTERESTS_URL, json={"interest_ids": [1, 2, 3]}, headers=headers)
        await client.put(MY_INTERESTS_URL, json={"interest_ids": [14]}, headers=headers)

        resp = await client.get(MY_INTERESTS_URL, headers=headers)
        names = {i["name"] for i in resp.json()["interests"]}
        assert names == {"Travel"}

    @pytest.mark.asyncio
    async def test_get_returns_empty_after_clear(self, client, mock_send_email, seed_interests):
        token = await _register_verify_login(client, mock_send_email, _USER)
        headers = {"Authorization": f"Bearer {token}"}

        await client.put(MY_INTERESTS_URL, json={"interest_ids": [1, 2]}, headers=headers)
        await client.put(MY_INTERESTS_URL, json={"interest_ids": []}, headers=headers)

        resp = await client.get(MY_INTERESTS_URL, headers=headers)
        assert resp.json()["interests"] == []


# ── Service unit tests ─────────────────────────────────────────────────────────


class TestInterestServiceUnit:
    @pytest.mark.asyncio
    async def test_set_user_interests_raises_422_for_unknown_id(self):
        mock_db = AsyncMock()
        svc = InterestService(mock_db)
        svc.repo = AsyncMock()
        # Repo returns only 1 interest even though 2 IDs were submitted
        svc.repo.get_by_ids.return_value = [Interest(id=1, name="Art")]

        with pytest.raises(HTTPException) as exc_info:
            await svc.set_user_interests(user_id=1, interest_ids=[1, 9999])

        assert exc_info.value.status_code == 422
        assert "INVALID_INTEREST_ID" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_set_user_interests_calls_repo_replace_on_success(self):
        mock_db = AsyncMock()
        svc = InterestService(mock_db)
        svc.repo = AsyncMock()
        saved = [Interest(id=1, name="Art"), Interest(id=2, name="Books")]
        svc.repo.get_by_ids.return_value = saved
        svc.repo.replace_user_interests.return_value = saved

        result = await svc.set_user_interests(user_id=42, interest_ids=[1, 2])

        svc.repo.replace_user_interests.assert_awaited_once_with(42, [1, 2])
        assert result is saved

    @pytest.mark.asyncio
    async def test_set_user_interests_empty_skips_validation(self):
        """Empty list bypasses get_by_ids and goes straight to replace."""
        mock_db = AsyncMock()
        svc = InterestService(mock_db)
        svc.repo = AsyncMock()
        svc.repo.replace_user_interests.return_value = []

        result = await svc.set_user_interests(user_id=1, interest_ids=[])

        svc.repo.get_by_ids.assert_not_awaited()
        svc.repo.replace_user_interests.assert_awaited_once_with(1, [])
        assert result == []
