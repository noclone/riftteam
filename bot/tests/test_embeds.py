import discord

from cogs.matchmaking import build_team_embed
from cogs.profile import build_profile_embed


class TestBuildProfileEmbed:
    def _player(self, **overrides):
        defaults = {
            "riot_game_name": "TestPlayer",
            "riot_tag_line": "EUW",
            "slug": "TestPlayer-EUW",
            "rank_solo_tier": "GOLD",
            "rank_solo_division": "II",
            "rank_solo_lp": 50,
            "rank_solo_wins": 60,
            "rank_solo_losses": 40,
            "rank_flex_tier": None,
            "rank_flex_division": None,
            "rank_flex_lp": None,
            "rank_flex_wins": None,
            "rank_flex_losses": None,
            "primary_role": "JUNGLE",
            "secondary_role": "MIDDLE",
            "discord_user_id": "123",
            "activities": ["SCRIMS"],
            "ambiance": "TRYHARD",
            "frequency_min": 3,
            "frequency_max": 5,
            "description": "Test description",
            "last_riot_sync": None,
            "champions": [],
        }
        defaults.update(overrides)
        return defaults

    def test_returns_embed(self):
        embed = build_profile_embed(self._player())
        assert isinstance(embed, discord.Embed)

    def test_title(self):
        embed = build_profile_embed(self._player())
        assert embed.title == "TestPlayer#EUW"

    def test_color_gold(self):
        embed = build_profile_embed(self._player())
        assert embed.color is not None
        assert embed.color.value == 0xFFD700

    def test_color_unranked(self):
        embed = build_profile_embed(self._player(rank_solo_tier=None))
        assert embed.color.value == 0x2B2D31

    def test_fields_present(self):
        embed = build_profile_embed(self._player())
        field_names = [f.name for f in embed.fields]
        assert "Rang Solo/Duo" in field_names
        assert "Rôle" in field_names
        assert "Stats externes" in field_names

    def test_rank_field_content(self):
        embed = build_profile_embed(self._player())
        rank_field = next(f for f in embed.fields if f.name == "Rang Solo/Duo")
        assert "Gold II" in rank_field.value
        assert "60% WR" in rank_field.value

    def test_flex_rank_shown(self):
        embed = build_profile_embed(self._player(
            rank_flex_tier="SILVER", rank_flex_division="I",
            rank_flex_lp=30, rank_flex_wins=20, rank_flex_losses=10,
        ))
        field_names = [f.name for f in embed.fields]
        assert "Rang Flex" in field_names

    def test_champions_field(self):
        champs = [
            {"champion_name": "Lee Sin", "games_played": 10, "wins": 7},
            {"champion_name": "Vi", "games_played": 5, "wins": 3},
        ]
        embed = build_profile_embed(self._player(champions=champs))
        field_names = [f.name for f in embed.fields]
        assert "Champions" in field_names

    def test_thumbnail_set(self):
        embed = build_profile_embed(self._player())
        assert embed.thumbnail.url is not None
        assert "gold" in embed.thumbnail.url

    def test_no_thumbnail_unranked(self):
        embed = build_profile_embed(self._player(rank_solo_tier=None))
        assert embed.thumbnail.url is None


class TestBuildTeamEmbed:
    def _team(self, **overrides):
        defaults = {
            "name": "Test Team",
            "slug": "test-team",
            "min_rank": "GOLD",
            "max_rank": "DIAMOND",
            "wanted_roles": ["JUNGLE", "MIDDLE"],
            "activities": ["SCRIMS"],
            "ambiance": "TRYHARD",
            "frequency_min": 3,
            "frequency_max": 5,
            "description": "Test team desc",
            "members": [],
        }
        defaults.update(overrides)
        return defaults

    def test_returns_embed(self):
        embed = build_team_embed(self._team())
        assert isinstance(embed, discord.Embed)

    def test_title(self):
        embed = build_team_embed(self._team())
        assert embed.title == "Test Team"

    def test_color_based_on_min_rank(self):
        embed = build_team_embed(self._team())
        assert embed.color.value == 0xFFD700

    def test_wanted_roles(self):
        embed = build_team_embed(self._team())
        field = next(f for f in embed.fields if f.name == "Rôles recherchés")
        assert "Jungle" in field.value
        assert "Mid" in field.value

    def test_elo_field(self):
        embed = build_team_embed(self._team())
        field_names = [f.name for f in embed.fields]
        assert "Elo" in field_names

    def test_roster_field(self):
        members = [
            {
                "role": "JUNGLE",
                "player": {
                    "riot_game_name": "Player1",
                    "riot_tag_line": "EUW",
                    "rank_solo_tier": "GOLD",
                    "rank_solo_division": "II",
                },
            }
        ]
        embed = build_team_embed(self._team(members=members))
        field_names = [f.name for f in embed.fields]
        assert any("Roster" in n for n in field_names)

    def test_no_ranks(self):
        embed = build_team_embed(self._team(min_rank=None, max_rank=None))
        field_names = [f.name for f in embed.fields]
        assert "Elo" not in field_names
