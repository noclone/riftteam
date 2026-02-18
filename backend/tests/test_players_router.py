from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import _make_player


class TestListPlayers:
    async def test_returns_200(self, app_client, mock_db):
        mock_result_count = MagicMock()
        mock_result_count.scalar_one.return_value = 0
        mock_result_list = MagicMock()
        mock_result_list.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result_count, mock_result_list])

        resp = await app_client.get("/api/players")
        assert resp.status_code == 200
        data = resp.json()
        assert "players" in data
        assert "total" in data


class TestGetPlayer:
    async def test_404_when_not_found(self, app_client, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        resp = await app_client.get("/api/players/nonexistent-slug")
        assert resp.status_code == 404


class TestCreatePlayer:
    async def test_no_token_returns_422(self, app_client, mock_db):
        resp = await app_client.post("/api/players", json={})
        assert resp.status_code == 422

    async def test_invalid_token_returns_403(self, app_client, mock_db):
        with patch("app.routers.players.consume_token", new_callable=AsyncMock, return_value=None):
            resp = await app_client.post(
                "/api/players",
                params={"token": "bad-token"},
                json={},
            )
            assert resp.status_code == 403


class TestUpdatePlayer:
    async def test_no_token_returns_422(self, app_client, mock_db):
        resp = await app_client.patch("/api/players/some-slug", json={})
        assert resp.status_code == 422

    async def test_invalid_token_returns_403(self, app_client, mock_db):
        with patch("app.routers.players.validate_token", new_callable=AsyncMock, return_value=None):
            resp = await app_client.patch(
                "/api/players/some-slug",
                params={"token": "bad-token"},
                json={},
            )
            assert resp.status_code == 403


class TestDeletePlayer:
    async def test_no_token_returns_422(self, app_client, mock_db):
        resp = await app_client.delete("/api/players/some-slug")
        assert resp.status_code == 422

    async def test_invalid_token_returns_403(self, app_client, mock_db):
        with patch("app.routers.players.validate_token", new_callable=AsyncMock, return_value=None):
            resp = await app_client.delete(
                "/api/players/some-slug",
                params={"token": "bad-token"},
            )
            assert resp.status_code == 403


class TestGetPlayerByDiscord:
    async def test_no_bot_secret_returns_422(self, app_client, mock_db):
        resp = await app_client.get("/api/players/by-discord/123")
        assert resp.status_code == 422

    async def test_wrong_bot_secret_returns_403(self, app_client, mock_db):
        resp = await app_client.get(
            "/api/players/by-discord/123",
            headers={"X-Bot-Secret": "wrong-secret"},
        )
        assert resp.status_code == 403


class TestRefreshPlayer:
    async def test_no_bot_secret_returns_422(self, app_client, mock_db):
        resp = await app_client.post("/api/players/some-slug/refresh")
        assert resp.status_code == 422

    async def test_wrong_bot_secret_returns_403(self, app_client, mock_db):
        resp = await app_client.post(
            "/api/players/some-slug/refresh",
            headers={"X-Bot-Secret": "wrong-secret"},
        )
        assert resp.status_code == 403
