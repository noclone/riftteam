import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.player import Player
from app.services.og_generator import generate_og_image
from shared.constants import RANK_COLORS, ROLE_NAMES

router = APIRouter()

CRAWLER_AGENTS = ("Discordbot", "Twitterbot", "facebookexternalhit", "Slackbot", "TelegramBot")
CACHE_TTL = 6 * 3600
_og_cache: dict[str, tuple[bytes, float]] = {}


def invalidate_og_cache(slug: str) -> None:
    _og_cache.pop(slug, None)


def _is_crawler(user_agent: str) -> bool:
    ua_lower = user_agent.lower()
    return any(bot.lower() in ua_lower for bot in CRAWLER_AGENTS)


def _format_rank(tier: str | None, division: str | None) -> str:
    if not tier:
        return "Unranked"
    label = tier.capitalize()
    if division and tier.upper() not in ("MASTER", "GRANDMASTER", "CHALLENGER"):
        label += f" {division}"
    return label


def _win_rate_str(wins: int | None, losses: int | None) -> str:
    w = wins or 0
    l = losses or 0
    if w + l == 0:
        return ""
    return f"{round(w / (w + l) * 100)}% WR"


def _theme_color(tier: str | None) -> str:
    hex_int = RANK_COLORS.get((tier or "").upper(), 0x6B6B6B)
    return f"#{hex_int:06x}"


def _build_og_html(player: Player) -> str:
    riot_id = f"{player.riot_game_name}#{player.riot_tag_line}"
    rank = _format_rank(player.rank_solo_tier, player.rank_solo_division)
    role = ROLE_NAMES.get(player.primary_role or "", "")

    title = f"{riot_id} — {rank}"
    if role:
        title += f" {role}"

    desc_parts = []
    wr = _win_rate_str(player.rank_solo_wins, player.rank_solo_losses)
    if wr:
        desc_parts.append(wr)
    top_champs = sorted(player.champions, key=lambda c: c.games_played, reverse=True)[:3]
    if top_champs:
        desc_parts.append(", ".join(c.champion_name for c in top_champs))
    if player.looking_for:
        labels = {"TEAM": "Cherche team", "DUO": "Cherche duo", "CLASH": "Cherche clash",
                  "SCRIM": "Cherche scrims", "ANY": "Cherche tout"}
        desc_parts.append(labels.get(player.looking_for, player.looking_for))
    description = " · ".join(desc_parts) if desc_parts else "Profil joueur LoL"

    og_image = f"{settings.api_url}/api/og/{player.slug}.png"
    profile_url = f"{settings.api_url}/p/{player.slug}"
    color = _theme_color(player.rank_solo_tier)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta property="og:type" content="website">
<meta property="og:site_name" content="RiftTeam">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{profile_url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{og_image}">
<meta name="theme-color" content="{color}">
<title>{title} — RiftTeam</title>
</head>
<body></body>
</html>"""


@router.get("/api/og/{slug}.png")
async def og_image(slug: str, db: AsyncSession = Depends(get_db)):
    slug_clean = slug.removesuffix(".png") if slug.endswith(".png") else slug
    cached = _og_cache.get(slug_clean)
    if cached:
        data, ts = cached
        if time.time() - ts < CACHE_TTL:
            return Response(content=data, media_type="image/png",
                            headers={"Cache-Control": f"public, max-age={CACHE_TTL}"})

    stmt = select(Player).options(selectinload(Player.champions)).where(Player.slug == slug_clean)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()
    if not player:
        return Response(status_code=404, content="Not found")

    player_dict = {
        "riot_game_name": player.riot_game_name,
        "riot_tag_line": player.riot_tag_line,
        "rank_solo_tier": player.rank_solo_tier,
        "rank_solo_division": player.rank_solo_division,
        "rank_solo_lp": player.rank_solo_lp,
        "rank_solo_wins": player.rank_solo_wins,
        "rank_solo_losses": player.rank_solo_losses,
        "primary_role": player.primary_role,
        "secondary_role": player.secondary_role,
        "profile_icon_id": player.profile_icon_id,
        "looking_for": player.looking_for,
    }
    champs = [
        {
            "champion_id": c.champion_id,
            "champion_name": c.champion_name,
            "games_played": c.games_played,
            "wins": c.wins,
            "losses": c.losses,
            "avg_kills": float(c.avg_kills) if c.avg_kills is not None else None,
            "avg_deaths": float(c.avg_deaths) if c.avg_deaths is not None else None,
            "avg_assists": float(c.avg_assists) if c.avg_assists is not None else None,
        }
        for c in player.champions
    ]

    png_bytes = await generate_og_image(player_dict, champs)
    _og_cache[slug_clean] = (png_bytes, time.time())

    return Response(content=png_bytes, media_type="image/png",
                    headers={"Cache-Control": f"public, max-age={CACHE_TTL}"})


@router.get("/p/{slug}")
async def profile_page(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    ua = request.headers.get("user-agent", "")
    if _is_crawler(ua):
        stmt = select(Player).options(selectinload(Player.champions)).where(Player.slug == slug)
        result = await db.execute(stmt)
        player = result.scalar_one_or_none()
        if not player:
            return Response(status_code=404, content="Not found")
        return HTMLResponse(_build_og_html(player))

    return RedirectResponse(f"{settings.app_url}/p/{slug}", status_code=302)
