from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_bot_secret
from app.models.guild_settings import GuildSettings

router = APIRouter(tags=["guild-settings"])


class GuildSettingsResponse(BaseModel):
    """Serialized guild settings."""

    guild_id: str
    announcement_channel_id: str | None = None

    model_config = {"from_attributes": True}


class GuildSettingsUpdate(BaseModel):
    """Payload for creating or updating guild settings."""

    announcement_channel_id: str | None = None


@router.get("/guild-settings/{guild_id}", response_model=GuildSettingsResponse)
async def get_guild_settings(guild_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve guild settings by guild ID."""
    result = await db.execute(
        select(GuildSettings).where(GuildSettings.guild_id == guild_id)
    )
    gs = result.scalar_one_or_none()
    if not gs:
        raise HTTPException(404, "Guild settings not found")
    return gs


@router.put("/guild-settings/{guild_id}", response_model=GuildSettingsResponse)
async def upsert_guild_settings(
    guild_id: str,
    body: GuildSettingsUpdate,
    _: str = Depends(verify_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    """Create or update guild settings (bot-only, authenticated)."""

    result = await db.execute(
        select(GuildSettings).where(GuildSettings.guild_id == guild_id)
    )
    gs = result.scalar_one_or_none()
    if gs:
        gs.announcement_channel_id = body.announcement_channel_id
    else:
        gs = GuildSettings(
            guild_id=guild_id,
            announcement_channel_id=body.announcement_channel_id,
        )
        db.add(gs)
    await db.commit()
    await db.refresh(gs)
    return gs
