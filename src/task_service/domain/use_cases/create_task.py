from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from task_service.infrastructure.redis.repository import RedisRepository
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
    ):
        self._database = database
        self._repository = repository
        self._publisher = publisher
        self._cache = cache

    @log(logger)
    async def execute(self, task: CreateTask) -> TaskSchema:
        """Создать задачу и отправить уведомление."""
        async with self._database.session() as session:
            created_task = await self._repository.create_task(session, task)

        # Сохраняем в кэш
        await self._cache.set_task(created_task)

        # Отправляем уведомление в RabbitMQ
        notification = TaskNotificationMessage(
            task_id=created_task.id,
            event_type=TaskEventType.CREATED,
            task_title=created_task.title,
            task_description=created_task.description,
            assignee=created_task.assignee,
            status=created_task.status,
            priority=created_task.priority,
            created_by=created_task.created_by,
        )
        await self._publisher.publish_task_notification(notification)

        logger.info(f"Task created: id={created_task.id}, title={created_task.title}")
        return created_task
