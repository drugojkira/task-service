"""ARQ Worker with CRON jobs for task-service."""

from arq import cron
from arq.connections import RedisSettings

from task_service.core.config import settings
from task_service.domain.tasks.auto_escalate_tasks import auto_escalate_tasks_task


class WorkerSettings:
    """ARQ worker settings."""

    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.ARQ_REDIS_DB,
        password=settings.REDIS_PASSWORD,
    )
    allow_abort_jobs = True

    cron_jobs = [
        cron(
            auto_escalate_tasks_task,
            name="auto_escalate_tasks",
            hour={9},
            minute={0},
        )
    ]

