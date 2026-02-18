from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestListTeams:
    async def test_returns_200(self, app_client, mock_db):
        mock_result_count = MagicMock()
        mock_result_count.scalar_one.return_value = 0
        mock_result_list = MagicMock()
        mock_result_list.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result_count, mock_result_list])

        resp = await app_client.get("/api/teams")
        assert resp.status_code == 200
        data = resp.json()
        assert "teams" in data
        assert "total" in data


class TestGetTeam:
    async def test_404_when_not_found(self, app_client, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = await app_client.get("/api/teams/nonexistent-slug")
        assert resp.status_code == 404


class TestCreateTeam:
    async def test_no_token_returns_422(self, app_client, mock_db):
        resp = await app_client.post("/api/teams", json={})
        assert resp.status_code == 422

    async def test_invalid_token_returns_403(self, app_client, mock_db):
        with patch("app.routers.teams.consume_token", new_callable=AsyncMock, return_value=None):
            resp = await app_client.post(
                "/api/teams",
                params={"token": "bad-token"},
                json={},
            )
            assert resp.status_code == 403


class TestAddMember:
    async def test_no_bot_secret_returns_422(self, app_client, mock_db):
        resp = await app_client.post(
            "/api/teams/some-team/members",
            json={"player_slug": "p-1", "discord_user_id": "123", "role": "JUNGLE"},
        )
        assert resp.status_code == 422

    async def test_wrong_bot_secret_returns_403(self, app_client, mock_db):
        resp = await app_client.post(
            "/api/teams/some-team/members",
            json={"player_slug": "p-1", "discord_user_id": "123", "role": "JUNGLE"},
            headers={"X-Bot-Secret": "wrong-secret"},
        )
        assert resp.status_code == 403


class TestRemoveMember:
    async def test_no_bot_secret_returns_422(self, app_client, mock_db):
        resp = await app_client.delete(
            "/api/teams/some-team/members/player-slug",
            params={"discord_user_id": "123"},
        )
        assert resp.status_code == 422

    async def test_wrong_bot_secret_returns_403(self, app_client, mock_db):
        resp = await app_client.delete(
            "/api/teams/some-team/members/player-slug",
            params={"discord_user_id": "123"},
            headers={"X-Bot-Secret": "wrong-secret"},
        )
        assert resp.status_code == 403
