import time

from app.routers.og import CACHE_MAX_SIZE, CACHE_TTL, _evict_cache, _is_crawler, _og_cache, _theme_color


class TestIsCrawler:
    def test_discordbot(self):
        assert _is_crawler("Discordbot/2.0") is True

    def test_twitterbot(self):
        assert _is_crawler("Twitterbot/1.0") is True

    def test_facebookbot(self):
        assert _is_crawler("facebookexternalhit/1.1") is True

    def test_slackbot(self):
        assert _is_crawler("Slackbot-LinkExpanding 1.0") is True

    def test_telegrambot(self):
        assert _is_crawler("TelegramBot") is True

    def test_real_browser(self):
        assert _is_crawler("Mozilla/5.0 (X11; Linux x86_64)") is False

    def test_empty_string(self):
        assert _is_crawler("") is False

    def test_case_insensitive(self):
        assert _is_crawler("DISCORDBOT/2.0") is True
        assert _is_crawler("discordbot/2.0") is True


class TestThemeColor:
    def test_gold(self):
        result = _theme_color("GOLD")
        assert result == "#ffd700"

    def test_iron(self):
        result = _theme_color("IRON")
        assert result == "#6b6b6b"

    def test_none(self):
        result = _theme_color(None)
        assert result == "#6b6b6b"

    def test_unknown_tier(self):
        result = _theme_color("UNKNOWN")
        assert result == "#6b6b6b"

    def test_lowercase_input(self):
        result = _theme_color("gold")
        assert result == "#ffd700"


class TestEvictCache:
    def setup_method(self):
        _og_cache.clear()

    def teardown_method(self):
        _og_cache.clear()

    def test_evicts_expired(self):
        _og_cache["old"] = (b"data", time.time() - CACHE_TTL - 1)
        _og_cache["fresh"] = (b"data", time.time())
        _evict_cache()
        assert "old" not in _og_cache
        assert "fresh" in _og_cache

    def test_evicts_by_size(self):
        now = time.time()
        for i in range(CACHE_MAX_SIZE + 10):
            _og_cache[f"key{i}"] = (b"data", now + i * 0.001)
        _evict_cache()
        assert len(_og_cache) <= CACHE_MAX_SIZE

    def test_keeps_fresh_entries(self):
        now = time.time()
        _og_cache["a"] = (b"data", now)
        _og_cache["b"] = (b"data", now + 1)
        _evict_cache()
        assert "a" in _og_cache
        assert "b" in _og_cache
