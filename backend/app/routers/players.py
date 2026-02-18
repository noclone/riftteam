import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session, get_db
from app.dependencies import get_riot_client, verify_bot_secret
from app.models.player import Player
from app.services.player_helpers import apply_riot_data, create_player_from_riot_data, populate_champions, refresh_champions
from app.routers.og import invalidate_og_cache
from app.schemas.player import (
    PlayerCreate,
    PlayerListResponse,
    PlayerResponse,
    PlayerUpdate,
)
from app.services.query_helpers import apply_rank_filters
from app.services.riot_api import fetch_full_profile
from app.services.snapshots import record_champion_snapshot, record_rank_snapshot, update_peak_rank
from app.services.sync import _sync_player_rank
from app.services.token_store import consume_token, validate_token
from shared.riot_client import RiotAPIError, RiotClient

logger = logging.getLogger("riftteam.players")

router = APIRouter(tags=["players"])

REFRESH_COOLDOWN = timedelta(hours=1)
LAZY_REFRESH_THRESHOLD = timedelta(hours=6)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def _get_player_or_404(slug: str, db: AsyncSession) -> Player:
    stmt = select(Player).options(selectinload(Player.champions)).where(Player.slug == slug)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(404, "Player not found")
    return player


@router.post("/players", response_model=PlayerResponse, status_code=201)
async def create_player(
    body: PlayerCreate,
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    token_data = await consume_token(db, token, "create")
    if token_data is None:
        raise HTTPException(403, "Token invalide ou expiré")

    game_name = token_data.game_name
    tag_line = token_data.tag_line
    if not game_name or not tag_line:
        raise HTTPException(400, "Token incomplet (game_name/tag_line manquant)")

    slug = Player.make_slug(game_name, tag_line)
    existing_result = await db.execute(
        select(Player).options(selectinload(Player.champions)).where(Player.slug == slug)
    )
    existing = existing_result.scalar_one_or_none()

    if existing and existing.discord_user_id is not None:
        raise HTTPException(409, "Profile already exists for this Riot ID")

    client = get_riot_client(request)
    try:
        riot_data = await fetch_full_profile(game_name, tag_line, client)
    except RiotAPIError as e:
        if e.status == 404:
            raise HTTPException(404, "Riot ID not found")
        raise HTTPException(502, f"Riot API error: {e.message}")

    now = datetime.now(timezone.utc)

    if existing and existing.discord_user_id is None:
        player = existing
        apply_riot_data(player, riot_data)
        player.discord_user_id = token_data.discord_user_id
        player.discord_username = token_data.discord_username
        player.description = body.description
        player.activities = body.activities
        player.ambiance = body.ambiance
        player.frequency_min = body.frequency_min
        player.frequency_max = body.frequency_max
        player.is_lft = body.is_lft
        player.last_riot_sync = now
        player.updated_at = now

        update_peak_rank(player, riot_data["rank_solo_tier"], riot_data["rank_solo_division"], riot_data["rank_solo_lp"])

        await refresh_champions(db, player, riot_data["champions"])
    else:
        player = create_player_from_riot_data(
            riot_data, slug,
            discord_user_id=token_data.discord_user_id,
            discord_username=token_data.discord_username,
            description=body.description,
            activities=body.activities,
            ambiance=body.ambiance,
            frequency_min=body.frequency_min,
            frequency_max=body.frequency_max,
            is_lft=body.is_lft,
            last_riot_sync=now,
        )

        populate_champions(player, riot_data["champions"])

        db.add(player)

    await db.flush()

    await record_rank_snapshot(db, player.id, riot_data, recorded_at=now)
    await record_champion_snapshot(
        db, player.id, riot_data["champions"],
        riot_data["primary_role"], riot_data["secondary_role"], recorded_at=now,
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Profile already exists for this Riot ID")
    await db.refresh(player)
    stmt = select(Player).options(selectinload(Player.champions)).where(Player.id == player.id)
    result = await db.execute(stmt)
    player = result.scalar_one()
    return player


_refreshing_players: set = set()


async def _lazy_rank_refresh(player_id, slug: str, riot_client: RiotClient) -> None:
    try:
        async with async_session() as db:
            stmt = select(Player).where(Player.id == player_id)
            result = await db.execute(stmt)
            player = result.scalar_one_or_none()
            if player:
                try:
                    await _sync_player_rank(player, riot_client)
                except Exception:
                    logger.exception("Lazy rank refresh failed for %s", slug)
    finally:
        _refreshing_players.discard(player_id)


@router.get("/players/by-discord/{discord_user_id}", response_model=PlayerResponse)
async def get_player_by_discord(
    discord_user_id: str,
    _: str = Depends(verify_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Player).options(selectinload(Player.champions)).where(Player.discord_user_id == discord_user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(404, "Player not found")
    return player


@router.get("/players/{slug}", response_model=PlayerResponse)
async def get_player(
    slug: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    player = await _get_player_or_404(slug, db)

    if player.last_riot_sync and player.id not in _refreshing_players:
        elapsed = datetime.now(timezone.utc) - _ensure_utc(player.last_riot_sync)
        if elapsed > LAZY_REFRESH_THRESHOLD:
            client = getattr(request.app.state, "riot_client", None)
            if client:
                _refreshing_players.add(player.id)
                background_tasks.add_task(_lazy_rank_refresh, player.id, player.slug, client)

    return player


@router.get("/players", response_model=PlayerListResponse)
async def list_players(
    is_lft: bool | None = Query(None),
    role: str | None = Query(None),
    min_rank: str | None = Query(None),
    max_rank: str | None = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Player).options(selectinload(Player.champions))
    count_stmt = select(func.count(Player.id))

    if is_lft is not None:
        stmt = stmt.where(Player.is_lft == is_lft)
        count_stmt = count_stmt.where(Player.is_lft == is_lft)
    if role:
        role_filter = or_(Player.primary_role == role.upper(), Player.secondary_role == role.upper())
        stmt = stmt.where(role_filter)
        count_stmt = count_stmt.where(role_filter)
    stmt, count_stmt = apply_rank_filters(stmt, count_stmt, min_rank, max_rank, Player.rank_solo_tier)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(Player.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    players = list(result.scalars().all())

    return PlayerListResponse(players=players, total=total)


@router.patch("/players/{slug}", response_model=PlayerResponse)
async def update_player(
    slug: str,
    body: PlayerUpdate,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    token_data = await validate_token(db, token)
    if token_data is None or token_data.action != "edit" or token_data.slug != slug:
        raise HTTPException(403, "Token invalide ou expiré")

    player = await _get_player_or_404(slug, db)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(player, field, value)
    player.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(player)
    stmt = select(Player).options(selectinload(Player.champions)).where(Player.id == player.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/players/{slug}/export")
async def export_player(
    slug: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    token_data = await validate_token(db, token)
    if token_data is None or token_data.action != "edit" or token_data.slug != slug:
        raise HTTPException(403, "Token invalide ou expiré")

    player = await _get_player_or_404(slug, db)
    data = PlayerResponse.model_validate(player).model_dump(mode="json")
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f'attachment; filename="riftteam-{slug}.json"'},
    )


@router.delete("/players/{slug}", status_code=204)
async def delete_player(
    slug: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    token_data = await validate_token(db, token)
    if token_data is None or token_data.action != "edit" or token_data.slug != slug:
        raise HTTPException(403, "Token invalide ou expiré")

    player = await _get_player_or_404(slug, db)
    await db.delete(player)
    await db.commit()


@router.post("/players/{slug}/refresh", response_model=PlayerResponse)
async def refresh_player(
    slug: str,
    request: Request,
    _: str = Depends(verify_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    player = await _get_player_or_404(slug, db)

    if player.last_riot_sync:
        elapsed = datetime.now(timezone.utc) - _ensure_utc(player.last_riot_sync)
        if elapsed < REFRESH_COOLDOWN:
            remaining = int((REFRESH_COOLDOWN - elapsed).total_seconds() / 60)
            raise HTTPException(429, f"Refresh cooldown: try again in {remaining} minutes")

    client = get_riot_client(request)
    try:
        riot_data = await fetch_full_profile(player.riot_game_name, player.riot_tag_line, client)
    except RiotAPIError as e:
        raise HTTPException(502, f"Riot API error: {e.message}")

    now = datetime.now(timezone.utc)
    apply_riot_data(player, riot_data)
    player.last_riot_sync = now
    player.updated_at = now

    update_peak_rank(player, riot_data["rank_solo_tier"], riot_data["rank_solo_division"], riot_data["rank_solo_lp"])

    await refresh_champions(db, player, riot_data["champions"])

    await record_rank_snapshot(db, player.id, riot_data, recorded_at=now)
    await record_champion_snapshot(
        db, player.id, riot_data["champions"],
        riot_data["primary_role"], riot_data["secondary_role"], recorded_at=now,
    )

    await db.commit()
    invalidate_og_cache(slug)
    await db.refresh(player)
    stmt = select(Player).options(selectinload(Player.champions)).where(Player.id == player.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.post("/players/{slug}/reactivate", status_code=200)
async def reactivate_player(
    slug: str,
    _: str = Depends(verify_bot_secret),
    discord_user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):

    player = await _get_player_or_404(slug, db)

    if player.discord_user_id != discord_user_id:
        raise HTTPException(403, "Not authorized")

    player.is_lft = True
    player.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "reactivated"}
