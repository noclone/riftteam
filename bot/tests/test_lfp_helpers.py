from cogs.lfp import _decode_filters, _encode_filters


class TestEncodeDecodeFilters:
    def test_round_trip_full(self):
        encoded = _encode_filters("JUNGLE", "GOLD", "DIAMOND")
        result = _decode_filters(encoded)
        assert result == ("JUNGLE", "GOLD", "DIAMOND")

    def test_round_trip_empty(self):
        encoded = _encode_filters(None, None, None)
        result = _decode_filters(encoded)
        assert result == (None, None, None)

    def test_round_trip_role_only(self):
        encoded = _encode_filters("JUNGLE", None, None)
        result = _decode_filters(encoded)
        assert result == ("JUNGLE", None, None)

    def test_round_trip_ranks_only(self):
        encoded = _encode_filters(None, "GOLD", "DIAMOND")
        result = _decode_filters(encoded)
        assert result == (None, "GOLD", "DIAMOND")

    def test_encode_format(self):
        encoded = _encode_filters("JUNGLE", "GOLD", "DIAMOND")
        assert encoded == "JUNGLE:GOLD:DIAMOND"

    def test_encode_nones(self):
        encoded = _encode_filters(None, None, None)
        assert encoded == "::"
