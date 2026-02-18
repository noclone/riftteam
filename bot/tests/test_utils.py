from unittest.mock import MagicMock

import aiohttp
import discord
import pytest

from utils import (
    build_info_parts,
    build_nav_view,
    build_no_results_msg,
    create_link_view,
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


class TestBuildInfoParts:
    def test_full_entity(self):
        entity = {
            "activities": ["SCRIMS", "TOURNOIS"],
            "ambiance": "TRYHARD",
            "frequency_min": 3,
            "frequency_max": 5,
        }
        parts = build_info_parts(entity)
        assert len(parts) == 3
        assert "Scrims" in parts[0]
        assert "Tournois" in parts[0]
        assert parts[1] == "Tryhard"
        assert "3-5x" in parts[2]

    def test_empty_entity(self):
        assert build_info_parts({}) == []

    def test_activities_only(self):
        entity = {"activities": ["LAN"]}
        parts = build_info_parts(entity)
        assert len(parts) == 1
        assert parts[0] == "LAN"

    def test_frequency_only(self):
        entity = {"frequency_min": 1, "frequency_max": 2}
        parts = build_info_parts(entity)
        assert len(parts) == 1
        assert "1-2x" in parts[0]

    def test_partial_frequency_ignored(self):
        entity = {"frequency_min": 1}
        assert build_info_parts(entity) == []


class TestCreateLinkView:
    @pytest.mark.asyncio
    async def test_creates_view_with_button(self):
        view = create_link_view("Click me", "https://example.com")
        assert len(view.children) == 1
        button = view.children[0]
        assert button.label == "Click me"
        assert button.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_button_style_is_link(self):
        view = create_link_view("Test", "https://example.com")
        button = view.children[0]
        assert button.style == discord.ButtonStyle.link


class TestBuildNavView:
    @pytest.mark.asyncio
    async def test_first_page(self):
        view = build_nav_view("prefix", 0, 15, 5, "filters")
        assert len(view.children) == 2
        prev_btn, next_btn = view.children
        assert prev_btn.disabled is True
        assert next_btn.disabled is False
        assert "prefix:-1:filters" in prev_btn.custom_id
        assert "prefix:1:filters" in next_btn.custom_id

    @pytest.mark.asyncio
    async def test_last_page(self):
        view = build_nav_view("prefix", 2, 15, 5, "filters")
        prev_btn, next_btn = view.children
        assert prev_btn.disabled is False
        assert next_btn.disabled is True

    @pytest.mark.asyncio
    async def test_middle_page(self):
        view = build_nav_view("prefix", 1, 15, 5, "filters")
        prev_btn, next_btn = view.children
        assert prev_btn.disabled is False
        assert next_btn.disabled is False

    @pytest.mark.asyncio
    async def test_single_page(self):
        view = build_nav_view("prefix", 0, 3, 5, "filters")
        prev_btn, next_btn = view.children
        assert prev_btn.disabled is True
        assert next_btn.disabled is True


class TestBuildNoResultsMsg:
    def test_no_filters(self):
        msg = build_no_results_msg("joueur LFT", None, None, None)
        assert msg == "Aucun joueur LFT trouvé."

    def test_with_role(self):
        msg = build_no_results_msg("joueur LFT", "JUNGLE", None, None)
        assert "Jungle" in msg
        assert "pour" in msg

    def test_with_ranks(self):
        msg = build_no_results_msg("équipe LFP", None, "GOLD", "DIAMOND")
        assert "Gold" in msg
        assert "Diamond" in msg

    def test_with_all_filters(self):
        msg = build_no_results_msg("joueur LFT", "TOP", "SILVER", "GOLD")
        assert "Top" in msg
        assert "Silver" in msg
        assert "Gold" in msg
