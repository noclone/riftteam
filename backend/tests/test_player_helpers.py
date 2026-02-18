from unittest.mock import MagicMock

from app.services.player_helpers import apply_riot_data, populate_champions


def _make_riot_data(**overrides):
    base = {
        "puuid": "abc123",
        "game_name": "TestPlayer",
        "tag_line": "EUW",
        "summoner_level": 150,
        "profile_icon_id": 4000,
        "rank_solo_tier": "GOLD",
        "rank_solo_division": "II",
        "rank_solo_lp": 50,
        "rank_solo_wins": 100,
        "rank_solo_losses": 90,
        "rank_flex_tier": "SILVER",
        "rank_flex_division": "I",
        "rank_flex_lp": 75,
        "rank_flex_wins": 30,
        "rank_flex_losses": 25,
        "primary_role": "JUNGLE",
        "secondary_role": "MIDDLE",
    }
    base.update(overrides)
    return base


def _make_player():
    player = MagicMock()
    player.champions = []
    return player


class TestApplyRiotData:
    def test_sets_all_fields(self):
        player = _make_player()
        riot_data = _make_riot_data()
        apply_riot_data(player, riot_data)

        assert player.riot_puuid == "abc123"
        assert player.riot_game_name == "TestPlayer"
        assert player.riot_tag_line == "EUW"
        assert player.summoner_level == 150
        assert player.profile_icon_id == 4000
        assert player.rank_solo_tier == "GOLD"
        assert player.rank_solo_division == "II"
        assert player.rank_solo_lp == 50
        assert player.rank_solo_wins == 100
        assert player.rank_solo_losses == 90
        assert player.rank_flex_tier == "SILVER"
        assert player.rank_flex_division == "I"
        assert player.rank_flex_lp == 75
        assert player.rank_flex_wins == 30
        assert player.rank_flex_losses == 25
        assert player.primary_role == "JUNGLE"
        assert player.secondary_role == "MIDDLE"

    def test_handles_none_values(self):
        player = _make_player()
        riot_data = _make_riot_data(
            rank_solo_tier=None,
            rank_solo_division=None,
            rank_solo_lp=None,
            secondary_role=None,
        )
        apply_riot_data(player, riot_data)

        assert player.rank_solo_tier is None
        assert player.secondary_role is None


class TestPopulateChampions:
    def test_adds_champions(self):
        player = _make_player()
        champs = [
            {
                "champion_id": 64,
                "champion_name": "Lee Sin",
                "mastery_level": 7,
                "mastery_points": 150000,
                "games_played": 20,
                "wins": 12,
                "losses": 8,
                "avg_kills": 7.5,
                "avg_deaths": 4.2,
                "avg_assists": 8.1,
            },
            {
                "champion_id": 254,
                "champion_name": "Vi",
                "mastery_level": 5,
                "mastery_points": 50000,
                "games_played": 10,
                "wins": 6,
                "losses": 4,
                "avg_kills": 6.0,
                "avg_deaths": 5.0,
                "avg_assists": 9.0,
            },
        ]
        populate_champions(player, champs)
        assert len(player.champions) == 2

    def test_empty_list(self):
        player = _make_player()
        populate_champions(player, [])
        assert len(player.champions) == 0
