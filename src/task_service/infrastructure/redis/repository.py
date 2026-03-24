from typing import Any

from pydantic import ValidationError
from redis.asyncio import Redis

from task_service.core.config import settings
from task_service.core.logger import get_logger
from task_service.schemas.task import TaskSchema, TaskStatistics

logger = get_logger(__name__)


class RedisRepository:
    """Redis репозиторий для кэширования задач."""

    _redis = Redis.from_url(
        settings.redis_url,
        db=settings.REDIS_DB,
        username=settings.REDIS_USERNAME,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
    )

    async def get_task(self, task_id: int) -> TaskSchema | None:
        """Получить задачу из кэша."""
        data = await self._redis.get(str(task_id))

        if not data:
            return None

        try:
            return TaskSchema.model_validate_json(data)
        except ValidationError:
            logger.warning(f"Invalid task data in cache: {task_id}")
            await self._redis.delete(str(task_id))
            return None

    async def set_task(self, task: TaskSchema, ex: int | None = None) -> None:
        """Сохранить задачу в кэш."""
        ttl = ex or settings.REDIS_CACHE_TTL
        await self._redis.set(
            name=str(task.id),
            value=task.model_dump_json(),
            ex=ttl,
        )

    async def delete_task(self, task_id: int) -> None:
        """Удалить задачу из кэша."""
        await self._redis.delete(str(task_id))

    async def get_task_statistics(self) -> TaskStatistics | None:
        """Получить статистику задач из кэша."""
        data = await self._redis.get("task_statistics")

        if not data:
            return None

        try:
            return TaskStatistics.model_validate_json(data)
        except ValidationError:
            logger.warning("Invalid task statistics data in cache")
            await self._redis.delete("task_statistics")
            return None

    async def set_task_statistics(self, statistics: TaskStatistics, ex: int = 60) -> None:
        """Сохранить статистику задач в кэш (TTL 1 минута по умолчанию)."""
        await self._redis.set(
            name="task_statistics",
            value=statistics.model_dump_json(),
            ex=ex,
        )

    async def delete_task_statistics(self) -> None:
        """Удалить статистику задач из кэша."""
        await self._redis.delete("task_statistics")

    async def clear_cache(self) -> None:
        """Очистить весь кэш."""
        await self._redis.flushdb()

    async def ping(self) -> Any:
        """Проверить соединение с Redis."""
        return await self._redis.ping()
