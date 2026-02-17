import asyncio
import time
from collections import deque

import aiohttp


class RiotAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"Riot API {status}: {message}")


_champion_id_to_name: dict[int, str] = {}


async def get_champion_names() -> dict[int, str]:
    if _champion_id_to_name:
        return _champion_id_to_name
    async with aiohttp.ClientSession() as session:
        async with session.get("https://ddragon.leagueoflegends.com/api/versions.json") as resp:
            versions = await resp.json()
        latest = versions[0]
        url = f"https://ddragon.leagueoflegends.com/cdn/{latest}/data/en_US/champion.json"
        async with session.get(url) as resp:
            data = await resp.json()
        for champ in data["data"].values():
            _champion_id_to_name[int(champ["key"])] = champ["name"]
    return _champion_id_to_name


CACHE_TTL = 300
CACHE_MAX_SIZE = 1000


class RiotClient:
    def __init__(
        self,
        api_key: str,
        requests_per_second: int = 18,
        requests_per_2min: int = 95,
    ):
        self.api_key = api_key
        self.base_url = "https://europe.api.riotgames.com"
        self.euw_url = "https://euw1.api.riotgames.com"
        self._short_window: deque[float] = deque()
        self._long_window: deque[float] = deque()
        self._rps = requests_per_second
        self._rpm = requests_per_2min
        self._lock = asyncio.Lock()
        self._cache: dict[str, tuple[dict | list, float]] = {}

    async def _wait_for_rate_limit(self) -> None:
        async with self._lock:
            now = time.monotonic()

            while self._short_window and now - self._short_window[0] > 1:
                self._short_window.popleft()
            while self._long_window and now - self._long_window[0] > 120:
                self._long_window.popleft()

            if len(self._short_window) >= self._rps:
                wait = 1 - (now - self._short_window[0])
                if wait > 0:
                    await asyncio.sleep(wait)

            if len(self._long_window) >= self._rpm:
                wait = 120 - (now - self._long_window[0])
                if wait > 0:
                    await asyncio.sleep(wait)

            now = time.monotonic()
            self._short_window.append(now)
            self._long_window.append(now)

    def _evict_cache(self) -> None:
        now = time.monotonic()
        expired = [k for k, (_, ts) in self._cache.items() if now - ts > CACHE_TTL]
        for k in expired:
            del self._cache[k]
        if len(self._cache) > CACHE_MAX_SIZE:
            oldest = sorted(self._cache, key=lambda k: self._cache[k][1])
            for k in oldest[: len(self._cache) - CACHE_MAX_SIZE]:
                del self._cache[k]

    async def _request(self, url: str) -> dict | list:
        cached = self._cache.get(url)
        if cached:
            data, ts = cached
            if time.monotonic() - ts < CACHE_TTL:
                return data

        await self._wait_for_rate_limit()
        async with aiohttp.ClientSession() as session:
            headers = {"X-Riot-Token": self.api_key}
            async with session.get(url, headers=headers) as resp:
                if resp.status == 429:
                    retry_after = int(resp.headers.get("Retry-After", 5))
                    await asyncio.sleep(retry_after)
                    return await self._request(url)
                if resp.status == 404:
                    raise RiotAPIError(404, "Not found")
                if resp.status >= 400:
                    text = await resp.text()
                    raise RiotAPIError(resp.status, text)
                result = await resp.json()

        self._cache[url] = (result, time.monotonic())
        self._evict_cache()
        return result

    async def get_account_by_riot_id(self, game_name: str, tag_line: str) -> dict:
        url = f"{self.base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        return await self._request(url)

    async def get_summoner_by_puuid(self, puuid: str) -> dict:
        url = f"{self.euw_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return await self._request(url)

    async def get_league_entries(self, puuid: str) -> list:
        url = f"{self.euw_url}/lol/league/v4/entries/by-puuid/{puuid}"
        return await self._request(url)

    async def get_top_masteries(self, puuid: str, count: int = 10) -> list:
        url = f"{self.euw_url}/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count={count}"
        return await self._request(url)

    async def get_match_ids(
        self, puuid: str, queue: int = 420, count: int = 20, start_time: int | None = None
    ) -> list:
        url = f"{self.base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?queue={queue}&count={count}"
        if start_time is not None:
            url += f"&startTime={start_time}"
        return await self._request(url)

    async def get_match(self, match_id: str) -> dict:
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}"
        return await self._request(url)
