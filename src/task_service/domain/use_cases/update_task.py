from typing import Optional

from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.postgres.task_history_repository import TaskHistoryRepository
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
        history_repository: Optional[TaskHistoryRepository] = None,
    ) -> None:
        self._database = database
        self._repository = repository
        self._publisher = publisher
        self._cache = cache
        self._kafka_publisher = kafka_publisher
        self._history_repository = history_repository

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

            # Логируем изменение в историю (diff)
            if self._history_repository:
                changes = self._build_diff(old_task, updated_task)
                if changes:
                    await self._history_repository.save(
                        session=session,
                        task_id=task_id,
                        changed_by=updated_by,
                        change_type="updated",
                        changes=changes,
                    )

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

    @staticmethod
    def _build_diff(old_task: TaskSchema, new_task: TaskSchema) -> dict:
        """Построить diff между старой и новой задачей."""
        diff = {}
        fields_to_compare = ["title", "description", "status", "priority", "assignee", "due_date"]
        for field in fields_to_compare:
            old_val = getattr(old_task, field)
            new_val = getattr(new_task, field)
            if old_val != new_val:
                # Приводим enum к строке для JSON-сериализации
                old_serialized = old_val.value if hasattr(old_val, 'value') else str(old_val) if old_val is not None else None
                new_serialized = new_val.value if hasattr(new_val, 'value') else str(new_val) if new_val is not None else None
                diff[field] = {"old": old_serialized, "new": new_serialized}
        return diff
