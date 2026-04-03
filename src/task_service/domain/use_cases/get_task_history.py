from typing import List, Optional

from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.task_history_repository import TaskHistoryRepository
from task_service.schemas.task_history import TaskHistoryFilters, TaskHistorySchema

logger = get_logger(__name__)


class GetTaskHistoryUseCase:
    """Use case для получения истории изменений задачи."""

    def __init__(
        self,
        database: Database,
        history_repository: TaskHistoryRepository,
    ) -> None:
        self._database = database
        self._history_repository = history_repository

    @log(logger)
    async def execute(
        self,
        task_id: int,
        filters: Optional[TaskHistoryFilters] = None,
    ) -> List[TaskHistorySchema]:
        """Получить историю изменений задачи."""
        async with self._database.session() as session:
            return await self._history_repository.get_by_task_id(
                session=session,
                task_id=task_id,
                filters=filters,
            )
