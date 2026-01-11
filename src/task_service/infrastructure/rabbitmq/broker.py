"""RabbitMQ broker singleton."""

from faststream.rabbit import RabbitBroker

from task_service.core.config import settings

# Глобальный broker
broker = RabbitBroker(settings.rabbitmq_url)



