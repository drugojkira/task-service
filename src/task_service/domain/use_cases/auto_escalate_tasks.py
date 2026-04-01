from __future__ import annotations

from dataclasses import dataclass

from task_service.core.config import settings
from task_service.core.logger import get_logger, log
from task_service.infrastructure.kafka.publisher import KafkaPublisher
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from task_service.infrastructure.redis.repository import RedisRepository
from task_service.schemas.task import TaskEventType, TaskNotificationMessage, TaskPriority, TaskSchema, UpdateTask

logger = get_logger(__name__)


@dataclass(frozen=True)
class EscalatedTask:
    task: TaskSchema
    old_priority: TaskPriority
    new_priority: TaskPriority


class AutoEscalateTasksUseCase:
    """Ежедневная автоподнялка приоритета для "залежавшихся" TODO задач."""

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

    @staticmethod
    def _next_priority(priority: TaskPriority) -> TaskPriority | None:
        if priority == TaskPriority.LOW:
            return TaskPriority.MEDIUM
        if priority == TaskPriority.MEDIUM:
            return TaskPriority.HIGH
        return None

    @log(logger)
    async def execute(self, *, older_than_days: int | None = None) -> dict[str, int]:
        days = older_than_days if older_than_days is not None else settings.AUTO_ESCALATE_TODO_AFTER_DAYS

        async with self._database.session() as session:
            candidates = await self._repository.get_tasks_for_auto_escalation(
                session,
                older_than_days=days,
            )

            escalated: list[EscalatedTask] = []
            for task in candidates:
                new_priority = self._next_priority(task.priority)
                if new_priority is None:
                    continue

                updated = await self._repository.update_task(
                    session,
                    task.id,
                    UpdateTask(priority=new_priority),
                )
                escalated.append(EscalatedTask(task=updated, old_priority=task.priority, new_priority=new_priority))

        if not escalated:
            logger.info("Auto escalation: no tasks to escalate")
            return {"checked": len(candidates), "escalated": 0}

        # Cache invalidation
        await self._cache.delete_task_statistics()
        for item in escalated:
            await self._cache.delete_task(item.task.id)
            await self._cache.set_task(item.task)

        # Publish events (RabbitMQ for email notifications, Kafka for analytics)
        for item in escalated:
            notification = TaskNotificationMessage(
                task_id=item.task.id,
                event_type=TaskEventType.PRIORITY_ESCALATED,
                task_title=item.task.title,
                task_description=item.task.description,
                assignee=item.task.assignee,
                status=item.task.status,
                priority=item.task.priority,
                created_by="system",
            )
            await self._publisher.publish_task_notification(notification)
            await self._kafka_publisher.publish_task_event(item.task, TaskEventType.PRIORITY_ESCALATED)

        logger.info(f"Auto escalation done: escalated={len(escalated)} checked={len(candidates)}")
        return {"checked": len(candidates), "escalated": len(escalated)}

