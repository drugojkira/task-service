from faststream.rabbit import RabbitBroker

from task_service.core.config import settings
from task_service.core.logger import get_logger, log
from task_service.schemas.task import TaskNotificationMessage

logger = get_logger(__name__)


class RabbitMQPublisher:
    """Публикатор сообщений в RabbitMQ."""

    def __init__(self, broker: RabbitBroker) -> None:
        self._broker = broker

    @log(logger)
    async def publish_task_notification(self, message: TaskNotificationMessage) -> None:
        """Отправить уведомление о задаче."""
        await self._broker.publish(
            message=message.model_dump_json().encode(),
            exchange=settings.RABBITMQ_EXCHANGE,
            routing_key=settings.RABBITMQ_ROUTING_KEY,
        )
        logger.info(f"Published notification: {message.event_type} for task {message.task_id}")
