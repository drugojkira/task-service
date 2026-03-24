from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.redis.repository import RedisRepository
from task_service.schemas.task import TaskStatistics

logger = get_logger(__name__)


class GetTaskStatisticsUseCase:
    """Use case для получения статистики задач."""

    def __init__(
        self,
        database: Database,
        repository: TaskRepository,
        cache: RedisRepository,
    ) -> None:
        self._database = database
        self._repository = repository
        self._cache = cache

    @log(logger)
    async def execute(self) -> TaskStatistics:
        """Получить статистику по задачам (с кэшированием)."""
        # Пробуем получить из кэша
        cached = await self._cache.get_task_statistics()
        if cached:
            logger.debug("Cache hit: task statistics")
            return cached

        # Получаем из БД
        async with self._database.session() as session:
            total_tasks = await self._repository.get_tasks_count(session)
            by_status = await self._repository.get_tasks_count_by_status(session)
            by_priority = await self._repository.get_tasks_count_by_priority(session)
            by_assignee = await self._repository.get_tasks_count_by_assignee(session)

        statistics = TaskStatistics(
            total_tasks=total_tasks,
            by_status=by_status,
            by_priority=by_priority,
            by_assignee=by_assignee,
        )

        # Сохраняем в кэш
        await self._cache.set_task_statistics(statistics)
        logger.debug("Cache miss: task statistics")

        return statistics