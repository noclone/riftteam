from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.guild_settings import GuildSettings

router = APIRouter(tags=["guild-settings"])


class GuildSettingsResponse(BaseModel):
    guild_id: str
    announcement_channel_id: str | None = None

    model_config = {"from_attributes": True}


class GuildSettingsUpdate(BaseModel):
    announcement_channel_id: str | None = None


@router.get("/guild-settings/{guild_id}", response_model=GuildSettingsResponse)
async def get_guild_settings(guild_id: str, db: AsyncSession = Depends(get_db)):
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
    x_bot_secret: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    if x_bot_secret != settings.bot_api_secret:
        raise HTTPException(403, "Invalid bot secret")

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
