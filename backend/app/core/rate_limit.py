from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import Settings


@dataclass(frozen=True)
class RateLimitRule:
    path_prefix: str
    max_requests: int
    window_seconds: int


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:  # type: ignore[override]
        super().__init__(app)
        self.settings = settings
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._rules = [
            RateLimitRule(
                path_prefix="/api/v1/auth/login",
                max_requests=min(settings.rate_limit_max_requests, 10),
                window_seconds=settings.rate_limit_window_seconds,
            ),
            RateLimitRule(
                path_prefix="/api/v1/orders/extract",
                max_requests=min(settings.rate_limit_max_requests, 30),
                window_seconds=settings.rate_limit_window_seconds,
            ),
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        rule = next((item for item in self._rules if request.url.path.startswith(item.path_prefix)), None)
        if rule is None:
            return await call_next(request)

        client_host = request.client.host if request.client else "unknown"
        bucket_key = f"{client_host}:{rule.path_prefix}"
        now = monotonic()
        window = self._buckets[bucket_key]

        while window and now - window[0] > rule.window_seconds:
            window.popleft()

        if len(window) >= rule.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry shortly."},
            )

        window.append(now)
        return await call_next(request)
