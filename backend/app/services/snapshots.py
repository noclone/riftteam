from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import Player
from app.models.snapshot import ChampionSnapshot, RankSnapshot
from app.services.rank_utils import is_higher_rank


async def record_rank_snapshot(
    db: AsyncSession,
    player_id,
    rank_data: dict,
    recorded_at: datetime | None = None,
) -> None:
    """Persist a rank snapshot for solo and flex queues."""
    ts = recorded_at or datetime.now(timezone.utc)

    for queue_type, prefix in [("RANKED_SOLO_5x5", "solo"), ("RANKED_FLEX_SR", "flex")]:
        tier = rank_data.get(f"rank_{prefix}_tier")
        if tier is None and prefix == "flex":
            continue
        snapshot = RankSnapshot(
            player_id=player_id,
            queue_type=queue_type,
            tier=tier,
            division=rank_data.get(f"rank_{prefix}_division"),
            lp=rank_data.get(f"rank_{prefix}_lp"),
            wins=rank_data.get(f"rank_{prefix}_wins"),
            losses=rank_data.get(f"rank_{prefix}_losses"),
            recorded_at=ts,
        )
        db.add(snapshot)


async def record_champion_snapshot(
    db: AsyncSession,
    player_id,
    champions: list[dict],
    primary_role: str | None,
    secondary_role: str | None,
    recorded_at: datetime | None = None,
) -> None:
    """Persist a champion pool snapshot with roles and stats."""
    ts = recorded_at or datetime.now(timezone.utc)
    snapshot = ChampionSnapshot(
        player_id=player_id,
        champions=champions,
        primary_role=primary_role,
        secondary_role=secondary_role,
        recorded_at=ts,
    )
    db.add(snapshot)


def update_peak_rank(player: Player, tier: str | None, division: str | None, lp: int | None) -> None:
    """Update the player's peak solo rank if the new rank is higher."""
    if is_higher_rank(tier, division, lp, player.peak_solo_tier, player.peak_solo_division, player.peak_solo_lp):
        player.peak_solo_tier = tier
        player.peak_solo_division = division
        player.peak_solo_lp = lp
