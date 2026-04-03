from typing import Optional

from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.postgres.task_history_repository import TaskHistoryRepository
from task_service.infrastructure.redis.repository import RedisRepository
from task_service.infrastructure.kafka.publisher import KafkaPublisher
from task_service.schemas.task import TaskEventType

logger = get_logger(__name__)


class DeleteTaskUseCase:
    """Use case для удаления задач."""

    def __init__(
        self,
        database: Database,
        repository: TaskRepository,
        cache: RedisRepository,
        kafka_publisher: KafkaPublisher,
        history_repository: Optional[TaskHistoryRepository] = None,
    ) -> None:
        self._database = database
        self._repository = repository
        self._cache = cache
        self._kafka_publisher = kafka_publisher
        self._history_repository = history_repository

    @log(logger)
    async def execute(self, task_id: int) -> None:
        """Удалить задачу по ID."""
        async with self._database.session() as session:
            # Получаем задачу перед удалением для события в Kafka
            task = await self._repository.get_one_task(session, task_id)

            # Логируем удаление в историю (до фактического удаления, т.к. FK CASCADE)
            if self._history_repository:
                await self._history_repository.save(
                    session=session,
                    task_id=task_id,
                    changed_by="system",
                    change_type="deleted",
                    changes=task.model_dump(mode="json"),
                )

            await self._repository.delete_task(session, task_id)

        # Удаляем из кэша
        await self._cache.delete_task(task_id)

        # Инвалидируем кэш статистики
        await self._cache.delete_task_statistics()

        # Отправляем событие в Kafka (для аналитики)
        await self._kafka_publisher.publish_task_event(task, TaskEventType.DELETED)

        logger.info(f"Task deleted: id={task_id}")
