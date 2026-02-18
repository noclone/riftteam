from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_riot_client, verify_bot_secret
from app.models.player import Player
from app.models.team import Team, TeamMember
from app.schemas.team import (
    RosterAddRequest,
    TeamCreate,
    TeamListResponse,
    TeamResponse,
    TeamUpdate,
)
from app.services.player_helpers import create_player_from_riot_data, populate_champions
from app.services.query_helpers import apply_rank_filters
from app.services.riot_api import fetch_full_profile
from app.services.token_store import consume_token, validate_token
from shared.riot_client import RiotAPIError

router = APIRouter(tags=["teams"])

VALID_ROLES = {"TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"}


async def _get_team_or_404(slug: str, db: AsyncSession) -> Team:
    """Load a team with roster by slug, or raise 404."""
    stmt = select(Team).options(selectinload(Team.members).selectinload(TeamMember.player)).where(Team.slug == slug)
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")
    return team


@router.post("/teams", response_model=TeamResponse, status_code=201)
async def create_team(
    body: TeamCreate,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Create a new team from a Discord bot token."""
    token_data = await consume_token(db, token, "team_create")
    if token_data is None:
        raise HTTPException(403, "Token invalide ou expiré")

    team_name = token_data.team_name
    if not team_name:
        raise HTTPException(400, "Token incomplet (team_name manquant)")

    slug = Team.make_slug(team_name)
    existing = await db.execute(select(Team).where(Team.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Une équipe avec le slug '{slug}' existe déjà")

    captain_check = await db.execute(select(Team).where(Team.captain_discord_id == token_data.discord_user_id))
    if captain_check.scalar_one_or_none():
        raise HTTPException(409, "Tu es déjà capitaine d'une équipe")

    now = datetime.now(UTC)
    team = Team(
        name=team_name,
        slug=slug,
        captain_discord_id=token_data.discord_user_id,
        captain_discord_name=token_data.discord_username,
        description=body.description,
        activities=body.activities,
        ambiance=body.ambiance,
        frequency_min=body.frequency_min,
        frequency_max=body.frequency_max,
        wanted_roles=body.wanted_roles,
        min_rank=body.min_rank,
        max_rank=body.max_rank,
        is_lfp=body.is_lfp,
        created_at=now,
        updated_at=now,
    )
    db.add(team)
    await db.commit()

    stmt = select(Team).options(selectinload(Team.members).selectinload(TeamMember.player)).where(Team.id == team.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/teams/by-captain/{discord_user_id}", response_model=TeamResponse)
async def get_team_by_captain(
    discord_user_id: str,
    _: str = Depends(verify_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    """Look up a team by its captain's Discord user ID (bot-only)."""
    stmt = (
        select(Team)
        .options(selectinload(Team.members).selectinload(TeamMember.player))
        .where(Team.captain_discord_id == discord_user_id)
    )
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")
    return team


@router.get("/teams/{slug}", response_model=TeamResponse)
async def get_team(
    slug: str,
    token: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return a team profile (hidden teams require a valid edit token)."""
    team = await _get_team_or_404(slug, db)

    if not team.is_lfp:
        token_data = (await validate_token(db, token)) if token else None
        if not token_data or token_data.action != "team_edit" or token_data.slug != slug:
            raise HTTPException(404, "Team not found")

    return team


@router.get("/teams", response_model=TeamListResponse)
async def list_teams(
    is_lfp: bool | None = Query(None),
    role: str | None = Query(None),
    min_rank: str | None = Query(None),
    max_rank: str | None = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List teams with optional LFP, wanted role and rank filters."""
    stmt = select(Team).options(selectinload(Team.members).selectinload(TeamMember.player))
    count_stmt = select(func.count(Team.id))

    if is_lfp is not None:
        stmt = stmt.where(Team.is_lfp == is_lfp)
        count_stmt = count_stmt.where(Team.is_lfp == is_lfp)
    if role:
        stmt = stmt.where(Team.wanted_roles.any(role.upper()))
        count_stmt = count_stmt.where(Team.wanted_roles.any(role.upper()))
    stmt, count_stmt = apply_rank_filters(stmt, count_stmt, min_rank, None, Team.min_rank, allow_null=True)
    stmt, count_stmt = apply_rank_filters(stmt, count_stmt, None, max_rank, Team.max_rank, allow_null=True)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(Team.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    teams = list(result.scalars().all())

    return TeamListResponse(teams=teams, total=total)


@router.get("/teams/check-name/{name}")
async def check_team_name(
    name: str,
    exclude_slug: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Check whether a team name (slug) is available."""
    slug = Team.make_slug(name)
    stmt = select(Team.id).where(Team.slug == slug)
    if exclude_slug:
        stmt = stmt.where(Team.slug != exclude_slug)
    result = await db.execute(stmt)
    return {"available": result.scalar_one_or_none() is None}


@router.patch("/teams/{slug}", response_model=TeamResponse)
async def update_team(
    slug: str,
    body: TeamUpdate,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Partially update team settings including name (requires edit token)."""
    token_data = await validate_token(db, token)
    if token_data is None or token_data.action != "team_edit" or token_data.slug != slug:
        raise HTTPException(403, "Token invalide ou expiré")

    team = await _get_team_or_404(slug, db)
    update_data = body.model_dump(exclude_unset=True)

    new_name = update_data.pop("name", None)
    if new_name is not None and new_name != team.name:
        new_slug = Team.make_slug(new_name)
        if new_slug != team.slug:
            conflict = await db.execute(select(Team.id).where(Team.slug == new_slug))
            if conflict.scalar_one_or_none():
                raise HTTPException(409, "Une équipe avec ce nom existe déjà")
            team.slug = new_slug
            token_data.slug = new_slug
        team.name = new_name

    for field, value in update_data.items():
        setattr(team, field, value)
    team.updated_at = datetime.now(UTC)
    await db.commit()

    stmt = select(Team).options(selectinload(Team.members).selectinload(TeamMember.player)).where(Team.id == team.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/teams/{slug}/export")
async def export_team(
    slug: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Download the full team profile as a JSON file."""
    token_data = await validate_token(db, token)
    if token_data is None or token_data.action != "team_edit" or token_data.slug != slug:
        raise HTTPException(403, "Token invalide ou expiré")

    team = await _get_team_or_404(slug, db)
    data = TeamResponse.model_validate(team).model_dump(mode="json")
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f'attachment; filename="riftteam-team-{slug}.json"'},
    )


@router.delete("/teams/{slug}", status_code=204)
async def delete_team(
    slug: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Delete a team permanently (requires edit token)."""
    token_data = await validate_token(db, token)
    if token_data is None or token_data.action != "team_edit" or token_data.slug != slug:
        raise HTTPException(403, "Token invalide ou expiré")

    team = await _get_team_or_404(slug, db)
    await db.delete(team)
    await db.commit()


@router.post("/teams/{slug}/members", response_model=TeamResponse)
async def add_member(
    slug: str,
    body: RosterAddRequest,
    request: Request,
    _: str = Depends(verify_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    """Add a player to the team roster, auto-creating the player if needed."""

    team = await _get_team_or_404(slug, db)

    if team.captain_discord_id != body.discord_user_id:
        raise HTTPException(403, "Seul le capitaine peut modifier le roster")

    if body.role.upper() not in VALID_ROLES:
        raise HTTPException(400, f"Rôle invalide. Choix : {', '.join(sorted(VALID_ROLES))}")

    stmt = select(Player).where(Player.slug == body.player_slug)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        name_parts = body.player_slug.split("-", 1)
        if len(name_parts) != 2:
            raise HTTPException(400, "Format de slug invalide (attendu: Pseudo-TAG)")

        game_name, tag_line = name_parts
        client = get_riot_client(request)
        try:
            riot_data = await fetch_full_profile(game_name, tag_line, client)
        except RiotAPIError as e:
            if e.status == 404:
                raise HTTPException(404, "Riot ID introuvable") from None
            raise HTTPException(502, f"Riot API error: {e.message}") from e

        now = datetime.now(UTC)
        player = create_player_from_riot_data(
            riot_data,
            Player.make_slug(riot_data["game_name"], riot_data["tag_line"]),
            discord_user_id=None,
            discord_username=None,
            is_lft=False,
            last_riot_sync=now,
        )

        populate_champions(player, riot_data["champions"])

        db.add(player)
        await db.flush()

    existing_membership = await db.execute(
        select(TeamMember).where(TeamMember.player_id == player.id)
    )
    if existing_membership.scalar_one_or_none():
        raise HTTPException(409, "Ce joueur est déjà membre d'une équipe")

    member = TeamMember(team_id=team.id, player_id=player.id, role=body.role.upper())
    db.add(member)
    team.updated_at = datetime.now(UTC)
    await db.commit()

    stmt = select(Team).options(selectinload(Team.members).selectinload(TeamMember.player)).where(Team.id == team.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.delete("/teams/{slug}/members/{player_slug}", status_code=204)
async def remove_member(
    slug: str,
    player_slug: str,
    _: str = Depends(verify_bot_secret),
    discord_user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Remove a player from the team roster (captain-only, bot-only)."""

    team = await _get_team_or_404(slug, db)

    if team.captain_discord_id != discord_user_id:
        raise HTTPException(403, "Seul le capitaine peut modifier le roster")

    player_stmt = select(Player).where(Player.slug == player_slug)
    player_result = await db.execute(player_stmt)
    player = player_result.scalar_one_or_none()
    if not player:
        raise HTTPException(404, "Joueur introuvable")

    member_stmt = select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.player_id == player.id)
    member_result = await db.execute(member_stmt)
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Ce joueur n'est pas dans l'équipe")

    await db.delete(member)
    team.updated_at = datetime.now(UTC)
    await db.commit()


@router.post("/teams/{slug}/reactivate", status_code=200)
async def reactivate_team(
    slug: str,
    _: str = Depends(verify_bot_secret),
    discord_user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Re-enable LFP status for an inactive team (captain-only, bot-only)."""

    team = await _get_team_or_404(slug, db)

    if team.captain_discord_id != discord_user_id:
        raise HTTPException(403, "Seul le capitaine peut réactiver l'équipe")

    team.is_lfp = True
    team.updated_at = datetime.now(UTC)
    await db.commit()
    return {"status": "reactivated"}
