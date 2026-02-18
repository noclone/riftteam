from datetime import datetime, timezone

from shared.constants import (
    MIN_GAMES_FOR_ROLE,
    QUEUE_NORMAL_DRAFT,
    QUEUE_RANKED_FLEX,
    QUEUE_RANKED_SOLO,
    SECONDARY_ROLE_THRESHOLD,
)
from shared.riot_client import RiotClient

MATCH_FETCH_LIMIT = 50


def _current_season_start() -> int:
    """Return the Unix timestamp for January 1st of the current year (UTC)."""
    now = datetime.now(timezone.utc)
    return int(datetime(now.year, 1, 1, tzinfo=timezone.utc).timestamp())


def _find_participant(match_data: dict, puuid: str) -> dict | None:
    """Extract the participant entry for a given PUUID from match data."""
    for participant in match_data["info"]["participants"]:
        if participant["puuid"] == puuid:
            return participant
    return None


def _process_matches(matches: list[dict], puuid: str) -> tuple[dict[str, int], dict[int, dict]]:
    """Aggregate role counts and per-champion stats from a list of matches."""
    role_counts: dict[str, int] = {
        "TOP": 0,
        "JUNGLE": 0,
        "MIDDLE": 0,
        "BOTTOM": 0,
        "UTILITY": 0,
    }
    champion_stats: dict[int, dict] = {}

    for match in matches:
        participant = _find_participant(match, puuid)
        if not participant:
            continue

        role = participant.get("teamPosition", "")
        if role in role_counts:
            role_counts[role] += 1

        champ_id = participant.get("championId", 0)
        if champ_id not in champion_stats:
            champion_stats[champ_id] = {
                "champion_name": participant["championName"],
                "games": 0,
                "wins": 0,
                "kills": 0,
                "deaths": 0,
                "assists": 0,
            }
        champion_stats[champ_id]["games"] += 1
        if participant["win"]:
            champion_stats[champ_id]["wins"] += 1
        champion_stats[champ_id]["kills"] += participant["kills"]
        champion_stats[champ_id]["deaths"] += participant["deaths"]
        champion_stats[champ_id]["assists"] += participant["assists"]

    return role_counts, champion_stats


async def fetch_ranked_matches(puuid: str, riot_client: RiotClient) -> list[dict]:
    """Fetch up to 50 matches, prioritising ranked solo then flex then normals."""
    match_ids = await riot_client.get_match_ids(
        puuid, queue=QUEUE_RANKED_SOLO, count=100, start_time=_current_season_start()
    )

    if len(match_ids) < MIN_GAMES_FOR_ROLE:
        flex_ids = await riot_client.get_match_ids(
            puuid, queue=QUEUE_RANKED_FLEX, count=100 - len(match_ids),
            start_time=_current_season_start(),
        )
        match_ids.extend(flex_ids)

    if len(match_ids) < MIN_GAMES_FOR_ROLE:
        normal_ids = await riot_client.get_match_ids(
            puuid, queue=QUEUE_NORMAL_DRAFT, count=100 - len(match_ids),
            start_time=_current_season_start(),
        )
        match_ids.extend(normal_ids)

    matches = []
    for match_id in match_ids[:MATCH_FETCH_LIMIT]:
        matches.append(await riot_client.get_match(match_id))
    return matches


async def detect_roles(
    puuid: str, matches: list[dict]
) -> tuple[str | None, str | None, dict[int, dict]]:
    """Determine primary/secondary roles and champion stats from match history."""
    role_counts, champion_stats = _process_matches(matches, puuid)

    sorted_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)
    primary_role = sorted_roles[0][0] if sorted_roles[0][1] > 0 else None

    total_games = sum(role_counts.values())
    secondary_role = None
    if total_games > 0 and sorted_roles[1][1] / total_games >= SECONDARY_ROLE_THRESHOLD:
        secondary_role = sorted_roles[1][0]

    return primary_role, secondary_role, champion_stats
