import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


def _make_player(**overrides):
    defaults = {
        "id": str(uuid.uuid4()),
        "slug": "TestPlayer-EUW",
        "riot_puuid": "fake-puuid",
        "riot_game_name": "TestPlayer",
        "riot_tag_line": "EUW",
        "region": "EUW1",
        "rank_solo_tier": "GOLD",
        "rank_solo_division": "II",
        "rank_solo_lp": 50,
        "rank_solo_wins": 60,
        "rank_solo_losses": 40,
        "rank_flex_tier": None,
        "rank_flex_division": None,
        "rank_flex_lp": None,
        "rank_flex_wins": None,
        "rank_flex_losses": None,
        "peak_solo_tier": "GOLD",
        "peak_solo_division": "II",
        "peak_solo_lp": 50,
        "primary_role": "JUNGLE",
        "secondary_role": "MIDDLE",
        "summoner_level": 200,
        "profile_icon_id": 1,
        "discord_user_id": "123456789",
        "discord_username": "testuser",
        "description": "Test player",
        "activities": ["SCRIMS"],
        "ambiance": "TRYHARD",
        "frequency_min": 3,
        "frequency_max": 5,
        "is_lft": True,
        "last_riot_sync": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "champions": [],
    }
    defaults.update(overrides)
    return defaults


def _make_team(**overrides):
    defaults = {
        "id": str(uuid.uuid4()),
        "slug": "test-team",
        "name": "Test Team",
        "captain_discord_id": "111111111",
        "captain_discord_name": "captain",
        "description": "A test team",
        "activities": ["SCRIMS"],
        "ambiance": "TRYHARD",
        "frequency_min": 3,
        "frequency_max": 5,
        "wanted_roles": ["JUNGLE", "MIDDLE"],
        "min_rank": "SILVER",
        "max_rank": "DIAMOND",
        "is_lfp": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "members": [],
    }
    defaults.update(overrides)
    return defaults


def _make_scrim(**overrides):
    defaults = {
        "id": str(uuid.uuid4()),
        "team_id": str(uuid.uuid4()),
        "captain_discord_id": "111111111",
        "min_rank": "SILVER",
        "max_rank": "DIAMOND",
        "scheduled_at": "2026-03-01T20:00:00+01:00",
        "format": "BO3",
        "game_count": None,
        "fearless": False,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "team": _make_team(),
    }
    defaults.update(overrides)
    return defaults


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_riot_client():
    client = AsyncMock()
    client.get_account_by_riot_id = AsyncMock()
    client.get_summoner_by_puuid = AsyncMock()
    client.get_league_entries = AsyncMock()
    client.get_champion_masteries = AsyncMock()
    client.get_match_ids = AsyncMock(return_value=[])
    client.get_match = AsyncMock()
    return client


@pytest.fixture
async def app_client(mock_db):
    from app.database import get_db
    from app.main import app

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
