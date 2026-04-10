from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.postgres.task_history_repository import TaskHistoryRepository
from task_service.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from task_service.infrastructure.redis.repository import RedisRepository
from typing import Optional

from task_service.infrastructure.kafka.publisher import KafkaPublisher
from task_service.schemas.task import (
    CreateTask,
    TaskEventType,
    TaskNotificationMessage,
    TaskSchema,
)

logger = get_logger(__name__)


class CreateTaskUseCase:
    """Use case для создания задачи."""

    def __init__(
        self,
        database: Database,
        repository: TaskRepository,
        publisher: RabbitMQPublisher,
        cache: RedisRepository,
        kafka_publisher: Optional[KafkaPublisher] = None,
        history_repository: Optional[TaskHistoryRepository] = None,
    ):
        self._database = database
        self._repository = repository
        self._publisher = publisher
        self._cache = cache
        self._kafka_publisher = kafka_publisher
        self._history_repository = history_repository

    @log(logger)
    async def execute(self, task: CreateTask) -> TaskSchema:
        """Создать задачу и отправить уведомление."""
        async with self._database.session() as session:
            created_task = await self._repository.create_task(session, task)

            # Логируем создание в историю
            if self._history_repository:
                await self._history_repository.save(
                    session=session,
                    task_id=created_task.id,
                    changed_by=task.created_by,
                    change_type="created",
                    changes=created_task.model_dump(mode="json"),
                )

        # Сохраняем в кэш
        await self._cache.set_task(created_task)

        # Инвалидируем кэш статистики
        await self._cache.delete_task_statistics()

        # Отправляем уведомление в RabbitMQ (для нотификаций) — всем assignees
        notification = TaskNotificationMessage(
            task_id=created_task.id,
            event_type=TaskEventType.CREATED,
            task_title=created_task.title,
            task_description=created_task.description,
            assignee=created_task.assignee,
            assignees=created_task.assignees,
            status=created_task.status,
            priority=created_task.priority,
            created_by=created_task.created_by,
        )
        await self._publisher.publish_task_notification(notification)

        # Отправляем событие в Kafka (для аналитики) если настроено
        if self._kafka_publisher is not None:
            await self._kafka_publisher.publish_task_event(created_task, TaskEventType.CREATED)

        logger.info(f"Task created: id={created_task.id}, title={created_task.title}")
        return created_task
