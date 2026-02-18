from app.services.rank_utils import is_higher_rank, rank_to_numeric


class TestRankToNumeric:
    def test_gold_ii_75(self):
        result = rank_to_numeric("GOLD", "II", 75)
        assert result > 0

    def test_unranked(self):
        assert rank_to_numeric(None, None, None) == -1

    def test_empty_string_tier(self):
        assert rank_to_numeric("", None, None) == -1

    def test_ordering(self):
        iron = rank_to_numeric("IRON", "IV", 0)
        gold = rank_to_numeric("GOLD", "II", 50)
        diamond = rank_to_numeric("DIAMOND", "I", 99)
        master = rank_to_numeric("MASTER", None, 200)
        assert iron < gold < diamond < master

    def test_division_ordering(self):
        g4 = rank_to_numeric("GOLD", "IV", 0)
        g3 = rank_to_numeric("GOLD", "III", 0)
        g2 = rank_to_numeric("GOLD", "II", 0)
        g1 = rank_to_numeric("GOLD", "I", 0)
        assert g4 < g3 < g2 < g1

    def test_lp_ordering(self):
        low = rank_to_numeric("GOLD", "II", 0)
        high = rank_to_numeric("GOLD", "II", 99)
        assert low < high

    def test_apex_no_division(self):
        master = rank_to_numeric("MASTER", None, 100)
        gm = rank_to_numeric("GRANDMASTER", None, 100)
        challenger = rank_to_numeric("CHALLENGER", None, 100)
        assert master < gm < challenger


class TestIsHigherRank:
    def test_diamond_higher_than_gold(self):
        assert is_higher_rank("DIAMOND", "IV", 0, "GOLD", "I", 99) is True

    def test_same_rank_lower_lp(self):
        assert is_higher_rank("GOLD", "IV", 0, "GOLD", "IV", 50) is False

    def test_same_rank_same_lp(self):
        assert is_higher_rank("GOLD", "II", 50, "GOLD", "II", 50) is False

    def test_gold_not_higher_than_diamond(self):
        assert is_higher_rank("GOLD", "I", 99, "DIAMOND", "IV", 0) is False

    def test_unranked_vs_ranked(self):
        assert is_higher_rank(None, None, None, "IRON", "IV", 0) is False

    def test_ranked_vs_unranked(self):
        assert is_higher_rank("IRON", "IV", 0, None, None, None) is True

    def test_both_unranked(self):
        assert is_higher_rank(None, None, None, None, None, None) is False

    def test_apex_tiers(self):
        assert is_higher_rank("CHALLENGER", None, 500, "GRANDMASTER", None, 500) is True
        assert is_higher_rank("GRANDMASTER", None, 500, "MASTER", None, 500) is True
