import time
from unittest.mock import MagicMock

from app.middleware.rate_limit import (
    CLEANUP_INTERVAL,
    MAX_REQUESTS,
    WINDOW_SECONDS,
    _buckets,
    _cleanup,
    _get_client_ip,
)


class TestCleanup:
    def setup_method(self):
        _buckets.clear()

    def teardown_method(self):
        _buckets.clear()

    def test_removes_expired_entries(self):
        import app.middleware.rate_limit as rl
        old_last = rl._last_cleanup
        rl._last_cleanup = time.monotonic() - CLEANUP_INTERVAL - 1
        try:
            _buckets["expired_ip"] = [time.monotonic() - WINDOW_SECONDS - 10]
            _buckets["active_ip"] = [time.monotonic()]
            _cleanup()
            assert "expired_ip" not in _buckets
            assert "active_ip" in _buckets
        finally:
            rl._last_cleanup = old_last


class TestGetClientIp:
    def test_x_forwarded_for(self):
        request = MagicMock()
        request.headers = {"x-forwarded-for": "1.2.3.4, 5.6.7.8"}
        assert _get_client_ip(request) == "1.2.3.4"

    def test_x_forwarded_for_single(self):
        request = MagicMock()
        request.headers = {"x-forwarded-for": "10.0.0.1"}
        assert _get_client_ip(request) == "10.0.0.1"

    def test_direct_client(self):
        request = MagicMock()
        request.headers = {}
        request.client.host = "192.168.1.1"
        assert _get_client_ip(request) == "192.168.1.1"

    def test_no_client(self):
        request = MagicMock()
        request.headers = {}
        request.client = None
        assert _get_client_ip(request) == "unknown"


class TestRateLimitFunctional:
    def setup_method(self):
        _buckets.clear()

    def teardown_method(self):
        _buckets.clear()

    def test_within_limit(self):
        ip = "test-ip"
        now = time.monotonic()
        _buckets[ip] = [now + i * 0.001 for i in range(MAX_REQUESTS - 1)]
        assert len(_buckets[ip]) < MAX_REQUESTS

    def test_exceeds_limit(self):
        ip = "test-ip"
        now = time.monotonic()
        _buckets[ip] = [now + i * 0.001 for i in range(MAX_REQUESTS)]
        assert len(_buckets[ip]) >= MAX_REQUESTS
