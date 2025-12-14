from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.redis.repository import RedisRepository

logger = get_logger(__name__)


class DeleteTaskUseCase:
    """Use case для удаления задач."""

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
    async def execute(self, task_id: int) -> None:
        """Удалить задачу по ID."""
        async with self._database.session() as session:
            await self._repository.delete_task(session, task_id)

        # Удаляем из кэша
        await self._cache.delete_task(task_id)

        logger.info(f"Task deleted: id={task_id}")
