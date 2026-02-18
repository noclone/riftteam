import pytest

from app.services.role_detector import _find_participant, _process_matches, detect_roles


def _make_match(puuid, role, champion_id=1, champion_name="Ahri", win=True,
                kills=5, deaths=3, assists=7):
    return {
        "info": {
            "participants": [
                {
                    "puuid": "other-puuid",
                    "teamPosition": "TOP",
                    "championId": 999,
                    "championName": "Garen",
                    "win": False,
                    "kills": 1,
                    "deaths": 5,
                    "assists": 2,
                },
                {
                    "puuid": puuid,
                    "teamPosition": role,
                    "championId": champion_id,
                    "championName": champion_name,
                    "win": win,
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                },
            ]
        }
    }


class TestFindParticipant:
    def test_found(self):
        match = _make_match("my-puuid", "JUNGLE")
        p = _find_participant(match, "my-puuid")
        assert p is not None
        assert p["puuid"] == "my-puuid"

    def test_not_found(self):
        match = _make_match("my-puuid", "JUNGLE")
        p = _find_participant(match, "unknown-puuid")
        assert p is None


class TestProcessMatches:
    def test_role_counting(self):
        puuid = "test"
        matches = (
            [_make_match(puuid, "JUNGLE")] * 7
            + [_make_match(puuid, "MIDDLE")] * 3
        )
        role_counts, _ = _process_matches(matches, puuid)
        assert role_counts["JUNGLE"] == 7
        assert role_counts["MIDDLE"] == 3
        assert role_counts["TOP"] == 0

    def test_champion_stats_accumulation(self):
        puuid = "test"
        matches = [
            _make_match(puuid, "JUNGLE", champion_id=64, champion_name="Lee Sin",
                        win=True, kills=10, deaths=2, assists=8),
            _make_match(puuid, "JUNGLE", champion_id=64, champion_name="Lee Sin",
                        win=False, kills=5, deaths=5, assists=3),
        ]
        _, champion_stats = _process_matches(matches, puuid)
        assert 64 in champion_stats
        lee = champion_stats[64]
        assert lee["champion_name"] == "Lee Sin"
        assert lee["games"] == 2
        assert lee["wins"] == 1
        assert lee["kills"] == 15
        assert lee["deaths"] == 7
        assert lee["assists"] == 11

    def test_no_matches(self):
        role_counts, champion_stats = _process_matches([], "test")
        assert sum(role_counts.values()) == 0
        assert champion_stats == {}


class TestDetectRoles:
    async def test_primary_and_secondary(self):
        puuid = "test"
        matches = (
            [_make_match(puuid, "JUNGLE")] * 8
            + [_make_match(puuid, "MIDDLE")] * 2
        )
        primary, secondary, stats = await detect_roles(puuid, matches)
        assert primary == "JUNGLE"
        assert secondary == "MIDDLE"

    async def test_no_secondary_below_threshold(self):
        puuid = "test"
        matches = (
            [_make_match(puuid, "TOP")] * 9
            + [_make_match(puuid, "MIDDLE")] * 1
        )
        primary, secondary, _ = await detect_roles(puuid, matches)
        assert primary == "TOP"
        assert secondary is None

    async def test_no_matches(self):
        primary, secondary, stats = await detect_roles("test", [])
        assert primary is None
        assert secondary is None
        assert stats == {}

    async def test_champion_stats_returned(self):
        puuid = "test"
        matches = [_make_match(puuid, "JUNGLE", champion_id=64, champion_name="Lee Sin")]
        _, _, stats = await detect_roles(puuid, matches)
        assert 64 in stats
