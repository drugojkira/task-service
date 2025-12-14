from task_service.domain.metrics.registry_metrics import (
    TASKS_BY_PRIORITY,
    TASKS_BY_STATUS,
    TASKS_TOTAL,
)
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository


class GetTasksMetricsUseCase:
    """Use case для обновления метрик задач."""

    def __init__(
        self,
        database: Database,
        repository: TaskRepository,
    ) -> None:
        self._database = database
        self._repository = repository

    async def execute(self) -> None:
        """Обновить все gauge метрики."""
        async with self._database.session() as session:
            # Общее количество
            total = await self._repository.get_total_tasks_count(session)
            TASKS_TOTAL.set(total)

            # По статусам
            status_counts = await self._repository.get_tasks_count_by_status(session)
            for status_value, count in status_counts.items():
                TASKS_BY_STATUS.labels(status=status_value).set(count)

            # По приоритетам
            priority_counts = await self._repository.get_tasks_count_by_priority(session)
            for priority_value, count in priority_counts.items():
                TASKS_BY_PRIORITY.labels(priority=priority_value).set(count)
