from unittest.mock import MagicMock

from app.services.snapshots import update_peak_rank


class TestUpdatePeakRank:
    def _make_player(self, tier, division, lp):
        p = MagicMock()
        p.peak_solo_tier = tier
        p.peak_solo_division = division
        p.peak_solo_lp = lp
        return p

    def test_updates_when_higher(self):
        player = self._make_player("GOLD", "II", 50)
        update_peak_rank(player, "DIAMOND", "IV", 0)
        assert player.peak_solo_tier == "DIAMOND"
        assert player.peak_solo_division == "IV"
        assert player.peak_solo_lp == 0

    def test_no_change_when_lower(self):
        player = self._make_player("DIAMOND", "IV", 0)
        update_peak_rank(player, "GOLD", "II", 99)
        assert player.peak_solo_tier == "DIAMOND"
        assert player.peak_solo_division == "IV"
        assert player.peak_solo_lp == 0

    def test_no_change_when_equal(self):
        player = self._make_player("GOLD", "II", 50)
        update_peak_rank(player, "GOLD", "II", 50)
        assert player.peak_solo_tier == "GOLD"
        assert player.peak_solo_division == "II"
        assert player.peak_solo_lp == 50

    def test_updates_from_unranked(self):
        player = self._make_player(None, None, None)
        update_peak_rank(player, "IRON", "IV", 0)
        assert player.peak_solo_tier == "IRON"

    def test_no_update_to_unranked(self):
        player = self._make_player("GOLD", "II", 50)
        update_peak_rank(player, None, None, None)
        assert player.peak_solo_tier == "GOLD"

    def test_both_unranked(self):
        player = self._make_player(None, None, None)
        update_peak_rank(player, None, None, None)
        assert player.peak_solo_tier is None

    def test_higher_lp_same_rank(self):
        player = self._make_player("GOLD", "II", 50)
        update_peak_rank(player, "GOLD", "II", 75)
        assert player.peak_solo_lp == 75
