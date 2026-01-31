"""Kafka publisher for task events."""

import json
from datetime import datetime
from uuid import uuid4

from aiokafka import AIOKafkaProducer

from task_service.core.logger import get_logger
from task_service.schemas.task import TaskEventType, TaskSchema

logger = get_logger(__name__)


class KafkaPublisher:
    """Publisher for sending task events to Kafka."""

    def __init__(self, bootstrap_servers: str, topic: str, enabled: bool = True) -> None:
        """Initialize Kafka publisher."""
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.enabled = enabled
        self.producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Start Kafka producer."""
        if not self.enabled:
            logger.info("Kafka publisher disabled")
            return

        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: v.encode("utf-8"),
        )
        await self.producer.start()
        logger.info(f"Kafka producer started: {self.bootstrap_servers}")

    async def stop(self) -> None:
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def publish_task_event(
        self, task: TaskSchema, event_type: TaskEventType
    ) -> None:
        """Publish task event to Kafka."""
        if not self.enabled:
            return

        if not self.producer:
            logger.error("Kafka producer not started")
            return

        try:
            event = {
                "event_id": str(uuid4()),
                "event_type": event_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "task_id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status.value,
                    "user_id": str(task.created_by) if task.created_by else None,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "metadata": {
                        "assignee": task.assignee,
                        "priority": task.priority.value if task.priority else None,
                    },
                },
            }

            await self.producer.send_and_wait(
                self.topic,
                value=json.dumps(event),
                key=str(task.id).encode("utf-8"),
            )

            logger.info(
                f"Task event published to Kafka: task_id={task.id}, "
                f"event_type={event_type.value}, topic={self.topic}"
            )

        except Exception as e:
            logger.error(
                f"Failed to publish task event to Kafka: task_id={task.id}, "
                f"event_type={event_type.value}, error={e}"
            )
            # Don't raise - Kafka is for analytics, not critical path
