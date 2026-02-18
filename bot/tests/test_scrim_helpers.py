from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from cogs.scrim import (
    _decode_filters,
    _encode_filters,
    _format_scrim_format,
    _parse_date,
    _parse_datetime,
    _parse_hour,
)

PARIS_TZ = ZoneInfo("Europe/Paris")


class TestParseDatetime:
    def test_basic(self):
        with patch("cogs.scrim.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 1, 10, 0, tzinfo=PARIS_TZ)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            dt = _parse_datetime("21/02", "20:00")
            assert dt.day == 21
            assert dt.month == 2
            assert dt.hour == 20
            assert dt.minute == 0

    def test_heure_h_format(self):
        with patch("cogs.scrim.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 1, 10, 0, tzinfo=PARIS_TZ)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            dt = _parse_datetime("21/02", "20h")
            assert dt.hour == 20
            assert dt.minute == 0

    def test_heure_h_minutes(self):
        with patch("cogs.scrim.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 1, 10, 0, tzinfo=PARIS_TZ)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            dt = _parse_datetime("21/02", "20h30")
            assert dt.hour == 20
            assert dt.minute == 30

    def test_explicit_year(self):
        with patch("cogs.scrim.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 1, 10, 0, tzinfo=PARIS_TZ)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            dt = _parse_datetime("21/02/2026", "20:00")
            assert dt.year == 2026
            assert dt.day == 21

    def test_invalid_date(self):
        with pytest.raises(ValueError):
            _parse_datetime("32/13", "20:00")

    def test_past_date_rolls_to_next_year(self):
        with patch("cogs.scrim.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 1, 10, 0, tzinfo=PARIS_TZ)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            dt = _parse_datetime("01/01", "10:00")
            assert dt.year == 2027


class TestParseDate:
    def test_basic(self):
        with patch("cogs.scrim.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 1, tzinfo=PARIS_TZ)
            result = _parse_date("21/02")
            assert result == "2026-02-21"

    def test_with_year(self):
        with patch("cogs.scrim.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 1, tzinfo=PARIS_TZ)
            result = _parse_date("15/03/2026")
            assert result == "2026-03-15"

    def test_invalid(self):
        with pytest.raises(ValueError):
            _parse_date("32/13")


class TestParseHour:
    def test_bare_number(self):
        assert _parse_hour("20") == 20

    def test_with_h(self):
        assert _parse_hour("20h") == 20

    def test_invalid_hour(self):
        with pytest.raises(ValueError):
            _parse_hour("25")

    def test_with_spaces(self):
        assert _parse_hour("  20h  ") == 20


class TestFormatScrimFormat:
    def test_bo3(self):
        assert _format_scrim_format("BO3", None, False) == "BO3"

    def test_game_count(self):
        assert _format_scrim_format(None, 5, False) == "5 games"

    def test_fearless(self):
        assert _format_scrim_format(None, 5, True) == "5 games · Fearless"

    def test_default(self):
        assert _format_scrim_format(None, None, False) == "BO1"

    def test_bo3_fearless(self):
        assert _format_scrim_format("BO3", None, True) == "BO3 · Fearless"


class TestEncodeDecodeFilters:
    def test_round_trip_full(self):
        encoded = _encode_filters("GOLD", "DIAMOND", "2026-03-01", "BO3", 18, 22)
        result = _decode_filters(encoded)
        assert result == ("GOLD", "DIAMOND", "2026-03-01", "BO3", 18, 22)

    def test_round_trip_empty(self):
        encoded = _encode_filters(None, None, None, None, None, None)
        result = _decode_filters(encoded)
        assert result == (None, None, None, None, None, None)

    def test_round_trip_partial(self):
        encoded = _encode_filters("GOLD", None, None, "BO1", None, None)
        result = _decode_filters(encoded)
        assert result == ("GOLD", None, None, "BO1", None, None)
