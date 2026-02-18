from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.token_store import consume_token, create_token, validate_token


def _make_token_obj(token="abc123", action="create", discord_user_id="999"):
    obj = MagicMock()
    obj.token = token
    obj.action = action
    obj.discord_user_id = discord_user_id
    obj.discord_username = "user"
    obj.game_name = "Player"
    obj.tag_line = "EUW"
    obj.slug = None
    obj.team_name = None
    obj.created_at = datetime.now(timezone.utc)
    return obj


class TestCreateToken:
    async def test_creates_token(self):
        db = AsyncMock()
        db.add = MagicMock()
        result = await create_token(
            db,
            action="create",
            discord_user_id="999",
            discord_username="user",
            game_name="Player",
            tag_line="EUW",
        )
        db.add.assert_called_once()
        assert result.action == "create"
        assert result.discord_user_id == "999"
        assert len(result.token) == 32


class TestValidateToken:
    async def test_returns_token(self):
        db = AsyncMock()
        token_obj = _make_token_obj()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = token_obj
        db.execute.return_value = mock_result

        result = await validate_token(db, "abc123")
        assert result is not None
        assert result.token == "abc123"

    async def test_returns_none_for_missing(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await validate_token(db, "nonexistent")
        assert result is None


class TestConsumeToken:
    async def test_consumes_and_deletes(self):
        db = AsyncMock()
        token_obj = _make_token_obj(action="create")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = token_obj
        db.execute.return_value = mock_result

        result = await consume_token(db, "abc123", "create")
        assert result is not None
        assert result.token == "abc123"
        db.delete.assert_called_once_with(token_obj)

    async def test_wrong_action_returns_none(self):
        db = AsyncMock()
        token_obj = _make_token_obj(action="create")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = token_obj
        db.execute.return_value = mock_result

        result = await consume_token(db, "abc123", "edit")
        assert result is None

    async def test_missing_token_returns_none(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await consume_token(db, "nonexistent", "create")
        assert result is None
