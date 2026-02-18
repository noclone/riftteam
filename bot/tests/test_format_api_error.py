from unittest.mock import MagicMock

import aiohttp

from utils import format_api_error


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
