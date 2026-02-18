from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlayerSummary(BaseModel):
    """Lightweight player info embedded in team member responses."""

    id: UUID
    slug: str
    riot_game_name: str
    riot_tag_line: str
    rank_solo_tier: str | None = None
    rank_solo_division: str | None = None
    rank_solo_lp: int | None = None
    primary_role: str | None = None
    profile_icon_id: int | None = None

    model_config = {"from_attributes": True}


class TeamMemberResponse(BaseModel):
    """A team member with their assigned role and player summary."""

    player: PlayerSummary
    role: str

    model_config = {"from_attributes": True}


class TeamCreate(BaseModel):
    """Fields submitted when creating a new team (excluding name and captain)."""

    description: str | None = Field(default=None, max_length=500)
    activities: list[str] = Field(default=[])
    ambiance: str | None = None
    frequency_min: int | None = None
    frequency_max: int | None = None
    wanted_roles: list[str] = Field(default=[])
    min_rank: str | None = None
    max_rank: str | None = None
    is_lfp: bool = True


class TeamUpdate(BaseModel):
    """Partial update of team settings (all optional)."""

    name: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    activities: list[str] | None = None
    ambiance: str | None = None
    frequency_min: int | None = None
    frequency_max: int | None = None
    wanted_roles: list[str] | None = None
    min_rank: str | None = None
    max_rank: str | None = None
    is_lfp: bool | None = None


class TeamResponse(BaseModel):
    """Full team profile with roster members."""

    id: UUID
    name: str
    slug: str
    captain_discord_id: str
    captain_discord_name: str | None = None
    description: str | None = None
    activities: list[str] | None = None
    ambiance: str | None = None
    frequency_min: int | None = None
    frequency_max: int | None = None
    wanted_roles: list[str] | None = None
    min_rank: str | None = None
    max_rank: str | None = None
    is_lfp: bool
    created_at: datetime
    updated_at: datetime
    members: list[TeamMemberResponse] = []

    model_config = {"from_attributes": True}


class TeamListResponse(BaseModel):
    """Paginated list of teams."""

    teams: list[TeamResponse]
    total: int


class RosterAddRequest(BaseModel):
    """Request body to add a player to a team roster."""

    player_slug: str
    role: str
    discord_user_id: str


class RosterRemoveRequest(BaseModel):
    """Request body to remove a player from a team roster."""

    discord_user_id: str
