import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from backend.app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # In-memory sliding window rate limiter by client IP and category
        self.request_records: Dict[str, List[float]] = defaultdict(list)

    def _get_limit_and_window(self, path: str, method: str) -> tuple[int, float]:
        if path == "/api/v1/portfolio/contact" and method == "POST":
            return (3, 3600.0)
        if path.startswith("/api/v1/portfolio/demos/") and path.endswith("/run") and method == "POST":
            return (10, 60.0)
        if path.startswith("/api/v1/auth/login") or path.startswith("/api/v1/auth/register"):
            return (settings.RATE_LIMIT_AUTH_PER_MINUTE, 60.0)
        if path.startswith("/api/v1/agents") or path.startswith("/api/v1/health") or path.startswith("/api/v1/portfolio"):
            return (settings.RATE_LIMIT_PUBLIC_PER_MINUTE, 60.0)
        return (settings.RATE_LIMIT_PER_MINUTE, 60.0)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Determine client identifier
        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")

        path = request.url.path
        limit, window_secs = self._get_limit_and_window(path, request.method.upper())
        key = f"{client_ip}:{request.method.upper()}:{path}"

        now = time.time()
        window_start = now - window_secs

        # Prune old records
        self.request_records[key] = [t for t in self.request_records[key] if t > window_start]

        if len(self.request_records[key]) >= limit:
            unit = "hour" if window_secs >= 3600 else "minute"
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded ({limit} requests/{unit}). Please try again later.",
                    "status_code": 429,
                },
                headers={"Retry-After": str(int(window_secs))},
            )

        self.request_records[key].append(now)
        response = await call_next(request)
        return response
