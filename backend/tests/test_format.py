from shared.format import format_rank, format_rank_range, format_win_rate


class TestFormatRank:
    def test_standard_rank(self):
        assert format_rank("GOLD", "II") == "Gold II"

    def test_rank_with_lp(self):
        assert format_rank("GOLD", "II", 75) == "Gold II (75 LP)"

    def test_apex_no_division(self):
        assert format_rank("MASTER", None, 350) == "Master (350 LP)"

    def test_grandmaster_no_division(self):
        assert format_rank("GRANDMASTER", None, 500) == "Grandmaster (500 LP)"

    def test_challenger_no_division(self):
        assert format_rank("CHALLENGER", None, 1000) == "Challenger (1000 LP)"

    def test_apex_division_ignored(self):
        result = format_rank("MASTER", "I", 350)
        assert "I" not in result.replace("Master", "")
        assert result == "Master (350 LP)"

    def test_unranked_none(self):
        assert format_rank(None, None) == "Unranked"

    def test_unranked_empty_string(self):
        assert format_rank("", None) == "Unranked"

    def test_rank_no_lp(self):
        assert format_rank("SILVER", "III") == "Silver III"

    def test_zero_lp(self):
        assert format_rank("IRON", "IV", 0) == "Iron IV (0 LP)"


class TestFormatWinRate:
    def test_standard(self):
        assert format_win_rate(60, 40) == "60% WR"

    def test_include_games(self):
        assert format_win_rate(60, 40, include_games=True) == "60% WR (100G)"

    def test_zero_games(self):
        assert format_win_rate(0, 0) == ""

    def test_none_values(self):
        assert format_win_rate(None, None) == ""

    def test_all_wins(self):
        assert format_win_rate(10, 0) == "100% WR"

    def test_all_losses(self):
        assert format_win_rate(0, 10) == "0% WR"

    def test_rounding(self):
        assert format_win_rate(1, 2) == "33% WR"


class TestFormatRankRange:
    def test_both_ranks(self):
        assert format_rank_range("GOLD", "DIAMOND") == "Gold → Diamond"

    def test_no_ranks(self):
        assert format_rank_range(None, None) == "Tous elos"

    def test_only_min(self):
        assert format_rank_range("GOLD", None) == "Gold"

    def test_only_max(self):
        assert format_rank_range(None, "DIAMOND") == "Diamond"

    def test_same_rank(self):
        assert format_rank_range("GOLD", "GOLD") == "Gold"

    def test_abbreviated(self):
        result = format_rank_range("GOLD", "DIAMOND", abbreviated=True)
        assert result == "Gold → Diam"

    def test_abbreviated_apex(self):
        result = format_rank_range("MASTER", "CHALLENGER", abbreviated=True)
        assert result == "Master → Chall"

    def test_abbreviated_single(self):
        result = format_rank_range("PLATINUM", None, abbreviated=True)
        assert result == "Plat"

    def test_abbreviated_none(self):
        assert format_rank_range(None, None, abbreviated=True) == "Tous elos"
