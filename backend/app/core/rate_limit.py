import time

import redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

_r = None


def redis_client():
    global _r
    if _r is None:
        if not settings.redis_url:
            raise RuntimeError("REDIS_URL not set")
        _r = redis.from_url(str(settings.redis_url))
    return _r


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        key = f"rl:{ip}:{int(time.time() // 3600)}"
        r = redis_client()
        count = r.incr(key)
        if count == 1:
            r.expire(key, 3600)

        if count > settings.rate_limit_per_hour:
            return JSONResponse(
                status_code=429,
                content={
                    "data": None,
                    "error": {"message": "Rate limit exceeded", "error_id": None},
                    "meta": {"limit": settings.rate_limit_per_hour},
                },
            )

        return await call_next(request)
