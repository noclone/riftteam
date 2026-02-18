from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import async_session, get_db
from app.models.champion import PlayerChampion
from app.models.player import Player
from app.routers.og import invalidate_og_cache
from app.schemas.player import (
    PlayerCreate,
    PlayerListResponse,
    PlayerResponse,
    PlayerUpdate,
)
from app.services.riot_api import fetch_full_profile
from app.services.snapshots import record_champion_snapshot, record_rank_snapshot, update_peak_rank
from app.services.sync import _sync_player_rank
from app.services.token_store import consume_token, validate_token
from shared.constants import RANK_ORDER
from shared.riot_client import RiotAPIError, RiotClient

router = APIRouter(tags=["players"])

REFRESH_COOLDOWN = timedelta(hours=1)
LAZY_REFRESH_THRESHOLD = timedelta(hours=6)


def _get_riot_client(request: Request) -> RiotClient:
    client = getattr(request.app.state, "riot_client", None)
    if client:
        return client
    if not settings.riot_api_key:
        raise HTTPException(503, "Riot API key not configured")
    return RiotClient(settings.riot_api_key)


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

    client = _get_riot_client(request)
    try:
        riot_data = await fetch_full_profile(game_name, tag_line, client)
    except RiotAPIError as e:
        if e.status == 404:
            raise HTTPException(404, "Riot ID not found")
        raise HTTPException(502, f"Riot API error: {e.message}")

    now = datetime.now(timezone.utc)

    if existing and existing.discord_user_id is None:
        player = existing
        player.riot_puuid = riot_data["puuid"]
        player.riot_game_name = riot_data["game_name"]
        player.riot_tag_line = riot_data["tag_line"]
        player.summoner_level = riot_data["summoner_level"]
        player.profile_icon_id = riot_data["profile_icon_id"]
        player.rank_solo_tier = riot_data["rank_solo_tier"]
        player.rank_solo_division = riot_data["rank_solo_division"]
        player.rank_solo_lp = riot_data["rank_solo_lp"]
        player.rank_solo_wins = riot_data["rank_solo_wins"]
        player.rank_solo_losses = riot_data["rank_solo_losses"]
        player.rank_flex_tier = riot_data["rank_flex_tier"]
        player.rank_flex_division = riot_data["rank_flex_division"]
        player.rank_flex_lp = riot_data["rank_flex_lp"]
        player.rank_flex_wins = riot_data["rank_flex_wins"]
        player.rank_flex_losses = riot_data["rank_flex_losses"]
        player.primary_role = riot_data["primary_role"]
        player.secondary_role = riot_data["secondary_role"]
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

        for champ in player.champions:
            await db.delete(champ)
        await db.flush()

        for champ in riot_data["champions"]:
            player.champions.append(
                PlayerChampion(
                    champion_id=champ["champion_id"],
                    champion_name=champ["champion_name"],
                    mastery_level=champ["mastery_level"],
                    mastery_points=champ["mastery_points"],
                    games_played=champ["games_played"],
                    wins=champ["wins"],
                    losses=champ["losses"],
                    avg_kills=champ["avg_kills"],
                    avg_deaths=champ["avg_deaths"],
                    avg_assists=champ["avg_assists"],
                )
            )
    else:
        player = Player(
            riot_puuid=riot_data["puuid"],
            riot_game_name=riot_data["game_name"],
            riot_tag_line=riot_data["tag_line"],
            slug=slug,
            summoner_level=riot_data["summoner_level"],
            profile_icon_id=riot_data["profile_icon_id"],
            rank_solo_tier=riot_data["rank_solo_tier"],
            rank_solo_division=riot_data["rank_solo_division"],
            rank_solo_lp=riot_data["rank_solo_lp"],
            rank_solo_wins=riot_data["rank_solo_wins"],
            rank_solo_losses=riot_data["rank_solo_losses"],
            rank_flex_tier=riot_data["rank_flex_tier"],
            rank_flex_division=riot_data["rank_flex_division"],
            rank_flex_lp=riot_data["rank_flex_lp"],
            rank_flex_wins=riot_data["rank_flex_wins"],
            rank_flex_losses=riot_data["rank_flex_losses"],
            peak_solo_tier=riot_data["rank_solo_tier"],
            peak_solo_division=riot_data["rank_solo_division"],
            peak_solo_lp=riot_data["rank_solo_lp"],
            primary_role=riot_data["primary_role"],
            secondary_role=riot_data["secondary_role"],
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

        for champ in riot_data["champions"]:
            player.champions.append(
                PlayerChampion(
                    champion_id=champ["champion_id"],
                    champion_name=champ["champion_name"],
                    mastery_level=champ["mastery_level"],
                    mastery_points=champ["mastery_points"],
                    games_played=champ["games_played"],
                    wins=champ["wins"],
                    losses=champ["losses"],
                    avg_kills=champ["avg_kills"],
                    avg_deaths=champ["avg_deaths"],
                    avg_assists=champ["avg_assists"],
                )
            )

        db.add(player)

    await db.flush()

    await record_rank_snapshot(db, player.id, riot_data, recorded_at=now)
    await record_champion_snapshot(
        db, player.id, riot_data["champions"],
        riot_data["primary_role"], riot_data["secondary_role"], recorded_at=now,
    )

    await db.commit()
    await db.refresh(player)
    stmt = select(Player).options(selectinload(Player.champions)).where(Player.id == player.id)
    result = await db.execute(stmt)
    player = result.scalar_one()
    return player


async def _lazy_rank_refresh(player_id, slug: str, riot_client: RiotClient) -> None:
    async with async_session() as db:
        stmt = select(Player).where(Player.id == player_id)
        result = await db.execute(stmt)
        player = result.scalar_one_or_none()
        if player:
            try:
                await _sync_player_rank(player, riot_client)
            except Exception:
                pass


@router.get("/players/by-discord/{discord_user_id}", response_model=PlayerResponse)
async def get_player_by_discord(
    discord_user_id: str,
    x_bot_secret: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    if x_bot_secret != settings.bot_api_secret:
        raise HTTPException(403, "Invalid bot secret")
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

    if player.last_riot_sync:
        elapsed = datetime.now(timezone.utc) - player.last_riot_sync.replace(tzinfo=timezone.utc)
        if elapsed > LAZY_REFRESH_THRESHOLD:
            player.last_riot_sync = datetime.now(timezone.utc)
            await db.commit()
            client = getattr(request.app.state, "riot_client", None)
            if client:
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
        stmt = stmt.where(Player.primary_role == role.upper())
        count_stmt = count_stmt.where(Player.primary_role == role.upper())
    if min_rank and min_rank.upper() in RANK_ORDER:
        min_val = RANK_ORDER[min_rank.upper()]
        valid_tiers = [t for t, v in RANK_ORDER.items() if v >= min_val]
        stmt = stmt.where(Player.rank_solo_tier.in_(valid_tiers))
        count_stmt = count_stmt.where(Player.rank_solo_tier.in_(valid_tiers))
    if max_rank and max_rank.upper() in RANK_ORDER:
        max_val = RANK_ORDER[max_rank.upper()]
        valid_tiers = [t for t, v in RANK_ORDER.items() if v <= max_val]
        stmt = stmt.where(Player.rank_solo_tier.in_(valid_tiers))
        count_stmt = count_stmt.where(Player.rank_solo_tier.in_(valid_tiers))

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
    x_bot_secret: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    if x_bot_secret != settings.bot_api_secret:
        raise HTTPException(403, "Invalid bot secret")
    player = await _get_player_or_404(slug, db)

    if player.last_riot_sync:
        elapsed = datetime.now(timezone.utc) - player.last_riot_sync.replace(tzinfo=timezone.utc)
        if elapsed < REFRESH_COOLDOWN:
            remaining = int((REFRESH_COOLDOWN - elapsed).total_seconds() / 60)
            raise HTTPException(429, f"Refresh cooldown: try again in {remaining} minutes")

    client = _get_riot_client(request)
    try:
        riot_data = await fetch_full_profile(player.riot_game_name, player.riot_tag_line, client)
    except RiotAPIError as e:
        raise HTTPException(502, f"Riot API error: {e.message}")

    now = datetime.now(timezone.utc)
    player.riot_puuid = riot_data["puuid"]
    player.riot_game_name = riot_data["game_name"]
    player.riot_tag_line = riot_data["tag_line"]
    player.summoner_level = riot_data["summoner_level"]
    player.profile_icon_id = riot_data["profile_icon_id"]
    player.rank_solo_tier = riot_data["rank_solo_tier"]
    player.rank_solo_division = riot_data["rank_solo_division"]
    player.rank_solo_lp = riot_data["rank_solo_lp"]
    player.rank_solo_wins = riot_data["rank_solo_wins"]
    player.rank_solo_losses = riot_data["rank_solo_losses"]
    player.rank_flex_tier = riot_data["rank_flex_tier"]
    player.rank_flex_division = riot_data["rank_flex_division"]
    player.rank_flex_lp = riot_data["rank_flex_lp"]
    player.rank_flex_wins = riot_data["rank_flex_wins"]
    player.rank_flex_losses = riot_data["rank_flex_losses"]
    player.primary_role = riot_data["primary_role"]
    player.secondary_role = riot_data["secondary_role"]
    player.last_riot_sync = now
    player.updated_at = now

    update_peak_rank(player, riot_data["rank_solo_tier"], riot_data["rank_solo_division"], riot_data["rank_solo_lp"])

    for champ in player.champions:
        await db.delete(champ)
    await db.flush()

    for champ in riot_data["champions"]:
        player.champions.append(
            PlayerChampion(
                champion_id=champ["champion_id"],
                champion_name=champ["champion_name"],
                mastery_level=champ["mastery_level"],
                mastery_points=champ["mastery_points"],
                games_played=champ["games_played"],
                wins=champ["wins"],
                losses=champ["losses"],
                avg_kills=champ["avg_kills"],
                avg_deaths=champ["avg_deaths"],
                avg_assists=champ["avg_assists"],
            )
        )

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
    x_bot_secret: str = Header(...),
    discord_user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if x_bot_secret != settings.bot_api_secret:
        raise HTTPException(403, "Invalid bot secret")

    player = await _get_player_or_404(slug, db)

    if player.discord_user_id != discord_user_id:
        raise HTTPException(403, "Not authorized")

    player.is_lft = True
    player.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "reactivated"}
