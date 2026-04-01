"""ARQ task for auto-escalating old TODO tasks."""

from task_service.core.config import settings
from task_service.core.logger import get_logger
from task_service.core.providers.setup import container
from task_service.domain.use_cases.auto_escalate_tasks import AutoEscalateTasksUseCase
from task_service.infrastructure.rabbitmq.broker import broker

logger = get_logger(__name__)


async def auto_escalate_tasks_task(ctx: dict) -> dict[str, int]:
    """ARQ entrypoint."""
    del ctx  # ARQ passes context; we don't use it currently.

    await broker.connect()
    try:
        async with container() as request_container:
            use_case = await request_container.get(AutoEscalateTasksUseCase)
            result = await use_case.execute(older_than_days=settings.AUTO_ESCALATE_TODO_AFTER_DAYS)
    finally:
        await broker.close()

    logger.info(f"ARQ auto_escalate_tasks_task result: {result}")
    return result

