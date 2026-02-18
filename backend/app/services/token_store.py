import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

TOKEN_TTL_SECONDS = 30 * 60


@dataclass
class TokenData:
    token: str
    action: Literal["create", "edit", "team_create", "team_edit"]
    discord_user_id: str
    discord_username: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    game_name: str | None = None
    tag_line: str | None = None
    slug: str | None = None
    team_name: str | None = None


_store: dict[str, TokenData] = {}


def _cleanup() -> None:
    now = datetime.now(timezone.utc)
    expired = [
        k for k, v in _store.items()
        if (now - v.created_at).total_seconds() > TOKEN_TTL_SECONDS
    ]
    for k in expired:
        del _store[k]


def create_token(
    action: Literal["create", "edit", "team_create", "team_edit"],
    discord_user_id: str,
    discord_username: str,
    game_name: str | None = None,
    tag_line: str | None = None,
    slug: str | None = None,
    team_name: str | None = None,
) -> TokenData:
    _cleanup()
    token = uuid.uuid4().hex
    data = TokenData(
        token=token,
        action=action,
        discord_user_id=discord_user_id,
        discord_username=discord_username,
        game_name=game_name,
        tag_line=tag_line,
        slug=slug,
        team_name=team_name,
    )
    _store[token] = data
    return data


def validate_token(token: str) -> TokenData | None:
    _cleanup()
    return _store.get(token)


def consume_token(token: str, expected_action: str) -> TokenData | None:
    _cleanup()
    data = _store.get(token)
    if data is None or data.action != expected_action:
        return None
    del _store[token]
    return data
