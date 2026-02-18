from cogs.profile import _champion_line, _rank_thumbnail, _role_display


class TestRoleDisplay:
    def test_both_roles(self):
        result = _role_display("JUNGLE", "MIDDLE")
        assert "Jungle" in result
        assert "Mid" in result
        assert "/" in result

    def test_single_role(self):
        result = _role_display("TOP", None)
        assert "Top" in result
        assert "/" not in result

    def test_no_role(self):
        assert _role_display(None, None) == "N/A"


class TestRankThumbnail:
    def test_gold(self):
        result = _rank_thumbnail("GOLD")
        assert result is not None
        assert "gold" in result
        assert result.endswith(".png")

    def test_none(self):
        assert _rank_thumbnail(None) is None


class TestChampionLine:
    def test_with_games(self):
        champ = {"champion_name": "Lee Sin", "games_played": 10, "wins": 7}
        result = _champion_line(champ)
        assert "Lee Sin" in result
        assert "70%" in result
        assert "10G" in result

    def test_no_games(self):
        champ = {"champion_name": "Lee Sin", "games_played": 0, "wins": 0}
        result = _champion_line(champ)
        assert result == "**Lee Sin**"

    def test_all_wins(self):
        champ = {"champion_name": "Ahri", "games_played": 5, "wins": 5}
        result = _champion_line(champ)
        assert "100%" in result
