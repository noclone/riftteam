from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.scrim import Scrim
from app.models.team import Team, TeamMember
from app.schemas.scrim import ScrimCreate, ScrimListResponse, ScrimResponse
from shared.constants import RANK_ORDER

router = APIRouter(tags=["scrims"])


async def _get_scrim_or_404(scrim_id: str, db: AsyncSession) -> Scrim:
    stmt = (
        select(Scrim)
        .options(selectinload(Scrim.team).selectinload(Team.members).selectinload(TeamMember.player))
        .where(Scrim.id == scrim_id)
    )
    result = await db.execute(stmt)
    scrim = result.scalar_one_or_none()
    if not scrim:
        raise HTTPException(404, "Scrim not found")
    return scrim


@router.post("/scrims", response_model=ScrimResponse, status_code=201)
async def create_scrim(
    body: ScrimCreate,
    x_bot_secret: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    if x_bot_secret != settings.bot_api_secret:
        raise HTTPException(403, "Invalid bot secret")

    stmt = (
        select(Team)
        .options(selectinload(Team.members).selectinload(TeamMember.player))
        .where(Team.slug == body.team_slug)
    )
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")

    if team.captain_discord_id != body.captain_discord_id:
        raise HTTPException(403, "Seul le capitaine peut poster un scrim")

    now = datetime.now(timezone.utc)

    previous = await db.execute(
        select(Scrim).where(Scrim.team_id == team.id, Scrim.is_active == True)
    )
    for old in previous.scalars().all():
        old.is_active = False
        old.updated_at = now
    scrim = Scrim(
        team_id=team.id,
        captain_discord_id=body.captain_discord_id,
        min_rank=body.min_rank,
        max_rank=body.max_rank,
        scheduled_at=body.scheduled_at,
        format=body.format,
        game_count=body.game_count,
        fearless=body.fearless,
        created_at=now,
        updated_at=now,
    )
    db.add(scrim)
    await db.commit()

    stmt = (
        select(Scrim)
        .options(selectinload(Scrim.team).selectinload(Team.members).selectinload(TeamMember.player))
        .where(Scrim.id == scrim.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


PARIS_TZ = ZoneInfo("Europe/Paris")


@router.get("/scrims", response_model=ScrimListResponse)
async def list_scrims(
    min_rank: str | None = Query(None),
    max_rank: str | None = Query(None),
    scheduled_date: str | None = Query(None),
    format: str | None = Query(None),
    hour_min: int | None = Query(None, ge=0, le=23),
    hour_max: int | None = Query(None, ge=0, le=23),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    base_filter = [Scrim.is_active == True, Scrim.scheduled_at >= now]

    stmt = (
        select(Scrim)
        .options(selectinload(Scrim.team).selectinload(Team.members).selectinload(TeamMember.player))
    )
    count_stmt = select(func.count(Scrim.id))

    for f in base_filter:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)

    if scheduled_date:
        try:
            d = date.fromisoformat(scheduled_date)
        except ValueError:
            raise HTTPException(400, "Format de date invalide (attendu : YYYY-MM-DD)")
        day_start = datetime.combine(d, time.min, tzinfo=PARIS_TZ)
        day_end = datetime.combine(d + timedelta(days=1), time.min, tzinfo=PARIS_TZ)
        stmt = stmt.where(Scrim.scheduled_at >= day_start, Scrim.scheduled_at < day_end)
        count_stmt = count_stmt.where(Scrim.scheduled_at >= day_start, Scrim.scheduled_at < day_end)

    paris_hour = extract("hour", func.timezone("Europe/Paris", Scrim.scheduled_at))
    if hour_min is not None:
        stmt = stmt.where(paris_hour >= hour_min)
        count_stmt = count_stmt.where(paris_hour >= hour_min)
    if hour_max is not None:
        stmt = stmt.where(paris_hour <= hour_max)
        count_stmt = count_stmt.where(paris_hour <= hour_max)

    if format:
        if format.startswith("G") and format[1:].isdigit():
            stmt = stmt.where(Scrim.game_count == int(format[1:]))
            count_stmt = count_stmt.where(Scrim.game_count == int(format[1:]))
        else:
            stmt = stmt.where(Scrim.format == format.upper())
            count_stmt = count_stmt.where(Scrim.format == format.upper())

    if min_rank and min_rank.upper() in RANK_ORDER:
        min_val = RANK_ORDER[min_rank.upper()]
        valid_tiers = [t for t, v in RANK_ORDER.items() if v >= min_val]
        stmt = stmt.where(Scrim.max_rank.in_(valid_tiers) | Scrim.max_rank.is_(None))
        count_stmt = count_stmt.where(Scrim.max_rank.in_(valid_tiers) | Scrim.max_rank.is_(None))

    if max_rank and max_rank.upper() in RANK_ORDER:
        max_val = RANK_ORDER[max_rank.upper()]
        valid_tiers = [t for t, v in RANK_ORDER.items() if v <= max_val]
        stmt = stmt.where(Scrim.min_rank.in_(valid_tiers) | Scrim.min_rank.is_(None))
        count_stmt = count_stmt.where(Scrim.min_rank.in_(valid_tiers) | Scrim.min_rank.is_(None))

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(Scrim.scheduled_at.asc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    scrims = list(result.scalars().all())

    return ScrimListResponse(scrims=scrims, total=total)


@router.delete("/scrims/{scrim_id}", status_code=204)
async def cancel_scrim(
    scrim_id: str,
    x_bot_secret: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    if x_bot_secret != settings.bot_api_secret:
        raise HTTPException(403, "Invalid bot secret")

    scrim = await _get_scrim_or_404(scrim_id, db)
    scrim.is_active = False
    scrim.updated_at = datetime.now(timezone.utc)
    await db.commit()
