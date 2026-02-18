from utils import decode_list_filters, encode_list_filters


class TestEncodeDecodeFilters:
    def test_round_trip_full(self):
        encoded = encode_list_filters("JUNGLE", "GOLD", "DIAMOND")
        result = decode_list_filters(encoded)
        assert result == ("JUNGLE", "GOLD", "DIAMOND")

    def test_round_trip_empty(self):
        encoded = encode_list_filters(None, None, None)
        result = decode_list_filters(encoded)
        assert result == (None, None, None)

    def test_round_trip_role_only(self):
        encoded = encode_list_filters("JUNGLE", None, None)
        result = decode_list_filters(encoded)
        assert result == ("JUNGLE", None, None)

    def test_round_trip_ranks_only(self):
        encoded = encode_list_filters(None, "GOLD", "DIAMOND")
        result = decode_list_filters(encoded)
        assert result == (None, "GOLD", "DIAMOND")

    def test_encode_format(self):
        encoded = encode_list_filters("JUNGLE", "GOLD", "DIAMOND")
        assert encoded == "JUNGLE:GOLD:DIAMOND"

    def test_encode_nones(self):
        encoded = encode_list_filters(None, None, None)
        assert encoded == "::"
