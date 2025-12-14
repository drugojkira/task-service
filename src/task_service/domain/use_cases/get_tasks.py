from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.redis.repository import RedisRepository
from task_service.schemas.task import TaskFilters, TaskSchema

logger = get_logger(__name__)


class GetTasksUseCase:
    """Use case для получения задач."""

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
    async def execute(
        self,
        filters: TaskFilters,
    ) -> tuple[list[TaskSchema], int]:
        """Получить список задач с фильтрацией."""
        async with self._database.session() as session:
            return await self._repository.get_all_tasks(session=session, filters=filters)

    @log(logger)
    async def get_by_id(self, task_id: int) -> TaskSchema:
        """Получить задачу по ID (с кэшированием)."""
        # Пробуем получить из кэша
        cached = await self._cache.get_task(task_id)
        if cached:
            logger.debug(f"Cache hit: task {task_id}")
            return cached

        # Получаем из БД
        async with self._database.session() as session:
            task = await self._repository.get_one_task(session, task_id)

        # Сохраняем в кэш
        await self._cache.set_task(task)
        logger.debug(f"Cache miss: task {task_id}")

        return task
