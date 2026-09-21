"""In-memory per-IP rate limit for POST /parse and POST /detect.

This is a single-process limiter for a portfolio demo dyno. It is not Redis,
not SlowAPI, and not shared across replicas. Disable with RATE_LIMIT_ENABLED=false.

X-Forwarded-For is trusted because Render/Railway/Fly terminate TLS in front of
the process. Direct access can spoof that header; that is an accepted demo limit.
"""

from __future__ import annotations

import os
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

DEFAULT_MAX_REQUESTS = 60
DEFAULT_WINDOW_SECONDS = 60
LIMITED_PATHS = frozenset({"/parse", "/detect"})

_lock = Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)


def rate_limit_enabled() -> bool:
    raw = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def rate_limit_max_requests() -> int:
    try:
        value = int(os.getenv("RATE_LIMIT_REQUESTS", str(DEFAULT_MAX_REQUESTS)))
    except ValueError:
        return DEFAULT_MAX_REQUESTS
    return max(1, value)


def rate_limit_window_seconds() -> int:
    try:
        value = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", str(DEFAULT_WINDOW_SECONDS)))
    except ValueError:
        return DEFAULT_WINDOW_SECONDS
    return max(1, value)


def rate_limit_config_summary() -> str:
    if not rate_limit_enabled():
        return "disabled"
    return f"{rate_limit_max_requests()}/{rate_limit_window_seconds()}s POST /parse,/detect"


def reset_rate_limit_state() -> None:
    """Clear buckets. Tests only."""
    with _lock:
        _hits.clear()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _should_limit(request: Request) -> bool:
    if not rate_limit_enabled():
        return False
    if request.method != "POST":
        return False
    path = request.url.path.rstrip("/") or "/"
    return path in LIMITED_PATHS


def allow_request(key: str, *, now: float | None = None) -> bool:
    """Record a hit. Return True if the request is allowed."""
    window = float(rate_limit_window_seconds())
    limit = rate_limit_max_requests()
    ts = monotonic() if now is None else now
    cutoff = ts - window
    with _lock:
        hits = _hits[key]
        while hits and hits[0] < cutoff:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(ts)
        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not _should_limit(request):
            return await call_next(request)

        if not allow_request(client_ip(request)):
            return JSONResponse(
                {"detail": "Rate limit exceeded."},
                status_code=429,
                headers={"Retry-After": str(rate_limit_window_seconds())},
            )
        return await call_next(request)
