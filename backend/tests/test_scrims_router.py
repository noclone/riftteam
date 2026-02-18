from unittest.mock import AsyncMock, MagicMock

import pytest


class TestListScrims:
    async def test_returns_200(self, app_client, mock_db):
        mock_result_count = MagicMock()
        mock_result_count.scalar_one.return_value = 0
        mock_result_list = MagicMock()
        mock_result_list.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[mock_result_count, mock_result_list])

        resp = await app_client.get("/api/scrims")
        assert resp.status_code == 200
        data = resp.json()
        assert "scrims" in data
        assert "total" in data


class TestCreateScrim:
    async def test_no_bot_secret_returns_422(self, app_client, mock_db):
        resp = await app_client.post("/api/scrims", json={
            "team_slug": "t",
            "captain_discord_id": "1",
            "scheduled_at": "2026-03-01T20:00:00+01:00",
        })
        assert resp.status_code == 422

    async def test_wrong_bot_secret_returns_403(self, app_client, mock_db):
        resp = await app_client.post(
            "/api/scrims",
            json={
                "team_slug": "t",
                "captain_discord_id": "1",
                "scheduled_at": "2026-03-01T20:00:00+01:00",
            },
            headers={"X-Bot-Secret": "wrong-secret"},
        )
        assert resp.status_code == 403


class TestCancelScrim:
    async def test_no_bot_secret_returns_422(self, app_client, mock_db):
        resp = await app_client.delete("/api/scrims/some-id")
        assert resp.status_code == 422

    async def test_wrong_bot_secret_returns_403(self, app_client, mock_db):
        resp = await app_client.delete(
            "/api/scrims/some-id",
            headers={"X-Bot-Secret": "wrong-secret"},
        )
        assert resp.status_code == 403
