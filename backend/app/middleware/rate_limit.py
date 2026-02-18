import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

MAX_REQUESTS = 60
WINDOW_SECONDS = 60
CLEANUP_INTERVAL = 300
CLEANUP_MAX_ENTRIES = 10_000

_buckets: dict[str, list[float]] = defaultdict(list)
_last_cleanup = time.monotonic()


def _cleanup() -> None:
    global _last_cleanup
    now = time.monotonic()
    if now - _last_cleanup < CLEANUP_INTERVAL:
        return
    _last_cleanup = now
    cutoff = now - WINDOW_SECONDS
    expired = [ip for ip, ts_list in _buckets.items() if not ts_list or ts_list[-1] < cutoff]
    for ip in expired:
        del _buckets[ip]
    if len(_buckets) > CLEANUP_MAX_ENTRIES:
        by_age = sorted(_buckets.items(), key=lambda item: item[1][-1] if item[1] else 0)
        for ip, _ in by_age[: len(_buckets) - CLEANUP_MAX_ENTRIES]:
            del _buckets[ip]


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "GET":
            return await call_next(request)

        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        if path == "/api/health":
            return await call_next(request)

        ip = _get_client_ip(request)
        now = time.monotonic()
        cutoff = now - WINDOW_SECONDS

        timestamps = _buckets[ip]
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

        if len(timestamps) >= MAX_REQUESTS:
            _cleanup()
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Try again later."},
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )

        timestamps.append(now)
        _cleanup()
        return await call_next(request)
