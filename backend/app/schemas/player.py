from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChampionResponse(BaseModel):
    champion_id: int
    champion_name: str
    mastery_level: int | None = None
    mastery_points: int | None = None
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    avg_kills: float | None = None
    avg_deaths: float | None = None
    avg_assists: float | None = None

    model_config = {"from_attributes": True}


class PlayerCreate(BaseModel):
    game_name: str = Field(max_length=16)
    tag_line: str = Field(max_length=5)
    discord_username: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    looking_for: str | None = None
    ambition: str | None = None
    languages: list[str] = Field(default=["fr"])
    availability: dict | None = None
    is_lft: bool = True


class PlayerUpdate(BaseModel):
    discord_username: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    looking_for: str | None = None
    ambition: str | None = None
    languages: list[str] | None = None
    availability: dict | None = None
    is_lft: bool | None = None


class PlayerResponse(BaseModel):
    id: UUID
    slug: str
    riot_puuid: str
    riot_game_name: str
    riot_tag_line: str
    region: str

    rank_solo_tier: str | None = None
    rank_solo_division: str | None = None
    rank_solo_lp: int | None = None
    rank_solo_wins: int | None = None
    rank_solo_losses: int | None = None
    rank_flex_tier: str | None = None
    rank_flex_division: str | None = None
    peak_solo_tier: str | None = None
    peak_solo_division: str | None = None
    peak_solo_lp: int | None = None
    primary_role: str | None = None
    secondary_role: str | None = None
    summoner_level: int | None = None
    profile_icon_id: int | None = None

    discord_username: str | None = None
    description: str | None = None
    looking_for: str | None = None
    ambition: str | None = None
    languages: list[str] | None = None
    availability: dict | None = None

    is_lft: bool
    last_riot_sync: datetime | None = None
    created_at: datetime
    updated_at: datetime

    champions: list[ChampionResponse] = []

    model_config = {"from_attributes": True}


class PlayerListResponse(BaseModel):
    players: list[PlayerResponse]
    total: int


class RiotCheckResponse(BaseModel):
    game_name: str
    tag_line: str
    puuid: str
    summoner_level: int | None = None
    profile_icon_id: int | None = None
