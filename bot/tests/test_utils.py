from unittest.mock import MagicMock

import aiohttp

from utils import (
    decode_list_filters,
    encode_list_filters,
    format_api_error,
    parse_riot_id,
)


class TestFormatApiError:
    def _make_client_response_error(self, status):
        exc = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=status,
            message="error",
        )
        return exc

    def test_429(self):
        exc = self._make_client_response_error(429)
        result = format_api_error(exc)
        assert "requêtes" in result.lower() or "minutes" in result.lower()

    def test_502(self):
        exc = self._make_client_response_error(502)
        result = format_api_error(exc)
        assert "indisponible" in result.lower()

    def test_503(self):
        exc = self._make_client_response_error(503)
        result = format_api_error(exc)
        assert "indisponible" in result.lower()

    def test_500(self):
        exc = self._make_client_response_error(500)
        result = format_api_error(exc)
        assert "erreur" in result.lower()

    def test_403(self):
        exc = self._make_client_response_error(403)
        result = format_api_error(exc)
        assert "autorisée" in result.lower() or "non" in result.lower()

    def test_client_error(self):
        exc = aiohttp.ClientError("connection failed")
        result = format_api_error(exc)
        assert "contacter" in result.lower() or "serveur" in result.lower()

    def test_generic_exception(self):
        exc = Exception("random")
        result = format_api_error(exc)
        assert "inattendue" in result.lower() or "erreur" in result.lower()


class TestParseRiotId:
    def test_valid(self):
        result = parse_riot_id("Pseudo#TAG")
        assert result == ("Pseudo", "TAG")

    def test_valid_with_spaces(self):
        result = parse_riot_id("Some Player#EUW")
        assert result == ("Some Player", "EUW")

    def test_no_hash(self):
        assert parse_riot_id("PseudoTAG") is None

    def test_empty_name(self):
        assert parse_riot_id("#TAG") is None

    def test_empty_tag(self):
        assert parse_riot_id("Pseudo#") is None

    def test_empty_string(self):
        assert parse_riot_id("") is None

    def test_multiple_hashes(self):
        result = parse_riot_id("Pseudo#TAG#Extra")
        assert result == ("Pseudo", "TAG#Extra")


class TestEncodeDecodeListFilters:
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

    def test_encode_format(self):
        encoded = encode_list_filters("JUNGLE", "GOLD", "DIAMOND")
        assert encoded == "JUNGLE:GOLD:DIAMOND"

    def test_encode_nones(self):
        encoded = encode_list_filters(None, None, None)
        assert encoded == "::"
