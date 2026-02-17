import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models.player import Player
from app.services.snapshots import record_rank_snapshot, update_peak_rank
from shared.riot_client import RiotAPIError, RiotClient

logger = logging.getLogger("riftteam.sync")


async def sync_active_ranks(client: RiotClient | None = None) -> int:
    if not client and not settings.riot_api_key:
        logger.warning("Skipping rank sync: no Riot API key configured")
        return 0

    client = client or RiotClient(settings.riot_api_key)
    synced = 0

    async with async_session() as db:
        stmt = select(Player).where(Player.is_lft == True)
        result = await db.execute(stmt)
        players = list(result.scalars().all())

    logger.info("Starting rank sync for %d active players", len(players))

    for player in players:
        try:
            await _sync_player_rank(player, client)
            synced += 1
        except RiotAPIError as e:
            logger.warning("Riot API error for %s: %s", player.slug, e.message)
        except Exception:
            logger.exception("Unexpected error syncing %s", player.slug)

    logger.info("Rank sync complete: %d/%d players updated", synced, len(players))
    return synced


async def _sync_player_rank(player: Player, client: RiotClient) -> None:
    summoner = await client.get_summoner_by_puuid(player.riot_puuid)
    entries = await client.get_league_entries(player.riot_puuid)

    rank_solo_tier = None
    rank_solo_division = None
    rank_solo_lp = None
    rank_solo_wins = None
    rank_solo_losses = None
    rank_flex_tier = None
    rank_flex_division = None
    rank_flex_lp = None
    rank_flex_wins = None
    rank_flex_losses = None

    for entry in entries:
        if entry["queueType"] == "RANKED_SOLO_5x5":
            rank_solo_tier = entry.get("tier")
            rank_solo_division = entry.get("rank")
            rank_solo_lp = entry.get("leaguePoints")
            rank_solo_wins = entry.get("wins")
            rank_solo_losses = entry.get("losses")
        elif entry["queueType"] == "RANKED_FLEX_SR":
            rank_flex_tier = entry.get("tier")
            rank_flex_division = entry.get("rank")
            rank_flex_lp = entry.get("leaguePoints")
            rank_flex_wins = entry.get("wins")
            rank_flex_losses = entry.get("losses")

    async with async_session() as db:
        stmt = select(Player).where(Player.id == player.id)
        result = await db.execute(stmt)
        p = result.scalar_one_or_none()
        if not p:
            return

        p.rank_solo_tier = rank_solo_tier
        p.rank_solo_division = rank_solo_division
        p.rank_solo_lp = rank_solo_lp
        p.rank_solo_wins = rank_solo_wins
        p.rank_solo_losses = rank_solo_losses
        p.rank_flex_tier = rank_flex_tier
        p.rank_flex_division = rank_flex_division
        p.rank_flex_lp = rank_flex_lp
        p.rank_flex_wins = rank_flex_wins
        p.rank_flex_losses = rank_flex_losses
        p.summoner_level = summoner.get("summonerLevel", p.summoner_level)
        p.last_riot_sync = datetime.now(timezone.utc)

        rank_data = {
            "rank_solo_tier": rank_solo_tier,
            "rank_solo_division": rank_solo_division,
            "rank_solo_lp": rank_solo_lp,
            "rank_solo_wins": rank_solo_wins,
            "rank_solo_losses": rank_solo_losses,
            "rank_flex_tier": rank_flex_tier,
            "rank_flex_division": rank_flex_division,
            "rank_flex_lp": rank_flex_lp,
            "rank_flex_wins": rank_flex_wins,
            "rank_flex_losses": rank_flex_losses,
        }
        await record_rank_snapshot(db, p.id, rank_data)
        update_peak_rank(p, rank_solo_tier, rank_solo_division, rank_solo_lp)

        await db.commit()
