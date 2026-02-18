from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.team import TeamResponse


class ScrimCreate(BaseModel):
    team_slug: str
    captain_discord_id: str
    min_rank: str | None = None
    max_rank: str | None = None
    scheduled_at: datetime
    format: str | None = Field(default=None, pattern=r"^(BO1|BO3|BO5)$")
    game_count: int | None = Field(default=None, ge=1, le=20)
    fearless: bool = False


class ScrimResponse(BaseModel):
    id: UUID
    team_id: UUID
    captain_discord_id: str
    min_rank: str | None = None
    max_rank: str | None = None
    scheduled_at: datetime
    format: str | None = None
    game_count: int | None = None
    fearless: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    team: TeamResponse

    model_config = {"from_attributes": True}


class ScrimListResponse(BaseModel):
    scrims: list[ScrimResponse]
    total: int
