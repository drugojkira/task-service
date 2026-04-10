"""Rate limiting middleware using Redis sliding window algorithm."""

import time

from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from task_service.core.config import settings
from task_service.core.logger import get_logger

logger = get_logger(__name__)

# Lua-скрипт для атомарного sliding window rate limiting
# Используем sorted set: score = timestamp, member = уникальный ID запроса
SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]

-- Удаляем устаревшие записи за пределами окна
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Считаем текущее количество запросов в окне
local current = redis.call('ZCARD', key)

if current < limit then
    -- Добавляем новый запрос
    redis.call('ZADD', key, now, member)
    -- Устанавливаем TTL на ключ = window (автоочистка)
    redis.call('EXPIRE', key, window)
    return {current + 1, limit, 0}
else
    -- Лимит превышен: вычисляем Retry-After
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 0
    if #oldest >= 2 then
        retry_after = math.ceil((tonumber(oldest[2]) + window) - now)
        if retry_after < 1 then retry_after = 1 end
    end
    return {current, limit, retry_after}
end
"""

# Пути, которые НЕ подлежат rate limiting
EXCLUDED_PATHS = {"/health", "/metrics", "/api/docs", "/api/redoc", "/api/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для ограничения частоты запросов (sliding window)."""

    def __init__(self, app, redis: Redis) -> None:
        super().__init__(app)
        self._redis = redis
        self._script_sha: str | None = None
        self._limit = settings.RATE_LIMIT_REQUESTS
        self._window = settings.RATE_LIMIT_WINDOW_SECONDS

    async def _get_script_sha(self) -> str:
        """Загрузить Lua-скрипт в Redis (кэшируется)."""
        if self._script_sha is None:
            self._script_sha = await self._redis.script_load(SLIDING_WINDOW_SCRIPT)
        return self._script_sha

    async def dispatch(self, request: Request, call_next) -> Response:
        # Пропускаем excluded пути
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"
        now = time.time()
        member = f"{now}:{id(request)}"

        try:
            sha = await self._get_script_sha()
            result = await self._redis.evalsha(
                sha, 1, key, str(now), str(self._window), str(self._limit), member
            )
            current_count, limit, retry_after = int(result[0]), int(result[1]), int(result[2])
        except Exception as e:
            # Если Redis недоступен — пропускаем (fail open)
            logger.warning(f"Rate limit check failed (allowing request): {e}")
            return await call_next(request)

        remaining = max(0, limit - current_count)

        if retry_after > 0:
            # Лимит превышен
            logger.warning(f"Rate limit exceeded for {client_ip}: {current_count}/{limit}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"},
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(retry_after),
                },
            )

        # Нормальный ответ с rate limit заголовками
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
