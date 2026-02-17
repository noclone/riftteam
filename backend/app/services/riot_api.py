from shared.riot_client import RiotClient, get_champion_names

from app.services.role_detector import detect_roles, fetch_ranked_matches


async def fetch_full_profile(game_name: str, tag_line: str, riot_client: RiotClient) -> dict:
    account = await riot_client.get_account_by_riot_id(game_name, tag_line)
    puuid = account["puuid"]

    summoner = await riot_client.get_summoner_by_puuid(puuid)
    league_entries = await riot_client.get_league_entries(puuid)
    id_to_name = await get_champion_names()

    rank_solo = {}
    rank_flex = {}
    for entry in league_entries:
        if entry["queueType"] == "RANKED_SOLO_5x5":
            rank_solo = entry
        elif entry["queueType"] == "RANKED_FLEX_SR":
            rank_flex = entry

    matches = await fetch_ranked_matches(puuid, riot_client)
    primary_role, secondary_role, champion_stats = await detect_roles(puuid, matches)

    champion_data = []
    for champ_id, stats in champion_stats.items():
        games = stats["games"]
        champion_data.append({
            "champion_id": champ_id,
            "champion_name": stats.get("champion_name") or id_to_name.get(champ_id, str(champ_id)),
            "mastery_level": None,
            "mastery_points": None,
            "games_played": games,
            "wins": stats["wins"],
            "losses": games - stats["wins"],
            "avg_kills": round(stats["kills"] / games, 1) if games > 0 else None,
            "avg_deaths": round(stats["deaths"] / games, 1) if games > 0 else None,
            "avg_assists": round(stats["assists"] / games, 1) if games > 0 else None,
        })

    masteries = await riot_client.get_top_masteries(puuid, count=10)
    mastery_map = {m["championId"]: m for m in masteries}
    for champ in champion_data:
        m = mastery_map.get(champ["champion_id"])
        if m:
            champ["mastery_level"] = m.get("championLevel")
            champ["mastery_points"] = m.get("championPoints")

    champion_data.sort(key=lambda c: c["games_played"], reverse=True)

    return {
        "puuid": puuid,
        "game_name": account.get("gameName", game_name),
        "tag_line": account.get("tagLine", tag_line),
        "summoner_level": summoner.get("summonerLevel"),
        "profile_icon_id": summoner.get("profileIconId"),
        "rank_solo_tier": rank_solo.get("tier"),
        "rank_solo_division": rank_solo.get("rank"),
        "rank_solo_lp": rank_solo.get("leaguePoints"),
        "rank_solo_wins": rank_solo.get("wins"),
        "rank_solo_losses": rank_solo.get("losses"),
        "rank_flex_tier": rank_flex.get("tier"),
        "rank_flex_division": rank_flex.get("rank"),
        "primary_role": primary_role,
        "secondary_role": secondary_role,
        "champions": champion_data,
    }
