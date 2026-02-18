from cogs.matchmaking import _format_roles, _format_wanted, _pick_role, _rank_in_range, _role_matches


class TestRankInRange:
    def test_in_range(self):
        assert _rank_in_range("GOLD", "SILVER", "DIAMOND") is True

    def test_below_range(self):
        assert _rank_in_range("IRON", "SILVER", "DIAMOND") is False

    def test_above_range(self):
        assert _rank_in_range("CHALLENGER", "SILVER", "DIAMOND") is False

    def test_unranked_with_range(self):
        assert _rank_in_range(None, "SILVER", "DIAMOND") is False

    def test_no_filter(self):
        assert _rank_in_range("GOLD", None, None) is True

    def test_only_min(self):
        assert _rank_in_range("GOLD", "SILVER", None) is True
        assert _rank_in_range("IRON", "SILVER", None) is False

    def test_only_max(self):
        assert _rank_in_range("GOLD", None, "DIAMOND") is True
        assert _rank_in_range("MASTER", None, "DIAMOND") is False

    def test_at_boundary(self):
        assert _rank_in_range("SILVER", "SILVER", "DIAMOND") is True
        assert _rank_in_range("DIAMOND", "SILVER", "DIAMOND") is True

    def test_unranked_no_filter(self):
        assert _rank_in_range(None, None, None) is True


class TestRoleMatches:
    def test_matches_primary(self):
        player = {"primary_role": "JUNGLE", "secondary_role": "MIDDLE"}
        assert _role_matches(player, ["JUNGLE", "TOP"]) is True

    def test_matches_secondary(self):
        player = {"primary_role": "JUNGLE", "secondary_role": "TOP"}
        assert _role_matches(player, ["TOP", "MIDDLE"]) is True

    def test_no_match(self):
        player = {"primary_role": "SUPPORT", "secondary_role": None}
        assert _role_matches(player, ["JUNGLE", "TOP"]) is False

    def test_no_wanted_roles(self):
        player = {"primary_role": "SUPPORT"}
        assert _role_matches(player, None) is True
        assert _role_matches(player, []) is True

    def test_no_player_roles(self):
        player = {"primary_role": None, "secondary_role": None}
        assert _role_matches(player, ["JUNGLE"]) is True


class TestPickRole:
    def test_primary_in_wanted(self):
        player = {"primary_role": "JUNGLE", "secondary_role": "MIDDLE"}
        assert _pick_role(player, ["JUNGLE", "TOP"]) == "JUNGLE"

    def test_secondary_in_wanted(self):
        player = {"primary_role": "SUPPORT", "secondary_role": "JUNGLE"}
        assert _pick_role(player, ["JUNGLE", "TOP"]) == "JUNGLE"

    def test_fallback_to_primary(self):
        player = {"primary_role": "SUPPORT", "secondary_role": "BOTTOM"}
        assert _pick_role(player, ["JUNGLE", "TOP"]) == "SUPPORT"

    def test_no_wanted_roles(self):
        player = {"primary_role": "JUNGLE", "secondary_role": "MIDDLE"}
        assert _pick_role(player, None) == "JUNGLE"

    def test_no_primary_fallback(self):
        player = {"primary_role": None, "secondary_role": None}
        assert _pick_role(player, ["JUNGLE"]) == "MIDDLE"


class TestFormatRoles:
    def test_both_roles(self):
        player = {"primary_role": "JUNGLE", "secondary_role": "MIDDLE"}
        result = _format_roles(player)
        assert "Jungle" in result
        assert "Mid" in result

    def test_single_role(self):
        player = {"primary_role": "TOP", "secondary_role": None}
        result = _format_roles(player)
        assert "Top" in result

    def test_no_roles(self):
        player = {"primary_role": None, "secondary_role": None}
        assert _format_roles(player) == "inconnu"


class TestFormatWanted:
    def test_single(self):
        result = _format_wanted(["JUNGLE"])
        assert result == "Jungle"

    def test_multiple(self):
        result = _format_wanted(["JUNGLE", "MIDDLE"])
        assert "Jungle" in result
        assert "Mid" in result
