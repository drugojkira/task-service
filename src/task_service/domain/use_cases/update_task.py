from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from task_service.infrastructure.redis.repository import RedisRepository
from task_service.infrastructure.kafka.publisher import KafkaPublisher
from task_service.schemas.task import (
    TaskEventType,
    TaskNotificationMessage,
    TaskSchema,
    UpdateTask,
)

logger = get_logger(__name__)


class UpdateTaskUseCase:
    """Use case для обновления задачи."""

    def __init__(
        self,
        database: Database,
        repository: TaskRepository,
        publisher: RabbitMQPublisher,
        cache: RedisRepository,
        kafka_publisher: KafkaPublisher,
    ) -> None:
        self._database = database
        self._repository = repository
        self._publisher = publisher
        self._cache = cache
        self._kafka_publisher = kafka_publisher

    @log(logger)
    async def execute(
        self,
        task: UpdateTask,
        task_id: int,
        updated_by: str,
    ) -> TaskSchema:
        """Обновить задачу и отправить уведомление."""
        async with self._database.session() as session:
            # Получаем старую задачу для сравнения
            old_task = await self._repository.get_one_task(session, task_id)

            updated_task = await self._repository.update_task(session, task_id, task)

        # Обновляем кэш
        await self._cache.delete_task(task_id)
        await self._cache.set_task(updated_task)

        # Инвалидируем кэш статистики
        await self._cache.delete_task_statistics()

        # Определяем тип события
        event_type = TaskEventType.UPDATED
        if task.status and old_task.status != task.status:
            event_type = TaskEventType.STATUS_CHANGED
        elif task.assignee and old_task.assignee != task.assignee:
            event_type = TaskEventType.ASSIGNED

        # Отправляем уведомление в RabbitMQ (для нотификаций)
        notification = TaskNotificationMessage(
            task_id=updated_task.id,
            event_type=event_type,
            task_title=updated_task.title,
            task_description=updated_task.description,
            assignee=updated_task.assignee,
            status=updated_task.status,
            priority=updated_task.priority,
            created_by=updated_by,
        )
        await self._publisher.publish_task_notification(notification)

        # Отправляем событие в Kafka (для аналитики)
        await self._kafka_publisher.publish_task_event(updated_task, event_type)

        logger.info(f"Task updated: id={updated_task.id}, event={event_type}")
        return updated_task
