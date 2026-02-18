from app.models.champion import PlayerChampion
from app.models.player import Player


def apply_riot_data(player: Player, riot_data: dict) -> None:
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


def populate_champions(player: Player, champions_data: list[dict]) -> None:
    for champ in champions_data:
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
