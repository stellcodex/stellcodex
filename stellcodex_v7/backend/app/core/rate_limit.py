from __future__ import annotations

import time
from typing import Optional

import redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

_r: Optional[redis.Redis] = None


def redis_client() -> redis.Redis:
    global _r
    if _r is None:
        if not settings.redis_url:
            raise RuntimeError("REDIS_URL not set")
        _r = redis.from_url(str(settings.redis_url))
    return _r


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        limit = int(getattr(settings, "rate_limit_per_hour", 0) or 0)
        if limit <= 0:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        key = f"rl:{ip}:{int(time.time() // 3600)}"

        try:
            r = redis_client()
            count = int(r.incr(key))
            if count == 1:
                r.expire(key, 3600)
        except Exception:
            # Fail-open to avoid taking down the API when Redis is unavailable.
            return await call_next(request)

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={
                    "data": None,
                    "error": {"message": "Rate limit exceeded", "error_id": None},
                    "meta": {"limit": limit},
                },
            )

        return await call_next(request)

