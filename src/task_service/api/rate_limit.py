"""Endpoint для проверки статуса rate limiting."""

import time

from fastapi import APIRouter, Request
from redis.asyncio import Redis

from task_service.core.config import settings
from task_service.core.logger import get_logger

logger = get_logger(__name__)

rate_limit_router = APIRouter(prefix="/rate-limit")


@rate_limit_router.get("/status")
async def get_rate_limit_status(request: Request) -> dict:
    """Проверить оставшиеся запросы для текущего IP."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"
    limit = settings.RATE_LIMIT_REQUESTS
    window = settings.RATE_LIMIT_WINDOW_SECONDS

    try:
        redis: Redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            username=settings.REDIS_USERNAME,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        now = time.time()
        # Удаляем устаревшие и считаем текущие
        await redis.zremrangebyscore(key, 0, now - window)
        current = await redis.zcard(key)
        await redis.aclose()
    except Exception as e:
        logger.warning(f"Rate limit status check failed: {e}")
        return {
            "client_ip": client_ip,
            "limit": limit,
            "window_seconds": window,
            "used": 0,
            "remaining": limit,
            "error": "Redis unavailable",
        }

    remaining = max(0, limit - current)

    return {
        "client_ip": client_ip,
        "limit": limit,
        "window_seconds": window,
        "used": current,
        "remaining": remaining,
    }
