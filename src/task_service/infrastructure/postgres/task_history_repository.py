from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.models import TaskHistory
from task_service.schemas.task_history import TaskHistoryFilters, TaskHistorySchema

logger = get_logger(__name__)


class TaskHistoryRepository:
    """Репозиторий для работы с историей изменений задач."""

    _collection = TaskHistory

    @log(logger)
    async def save(
        self,
        session: AsyncSession,
        task_id: int,
        changed_by: str,
        change_type: str,
        changes: dict,
    ) -> TaskHistorySchema:
        """Сохранить запись истории изменения задачи."""
        query = (
            insert(self._collection)
            .values(
                task_id=task_id,
                changed_by=changed_by,
                change_type=change_type,
                changes=changes,
            )
            .returning(self._collection)
        )
        result = await session.scalar(query)
        await session.flush()
        return TaskHistorySchema.model_validate(result)

    @log(logger)
    async def get_by_task_id(
        self,
        session: AsyncSession,
        task_id: int,
        filters: Optional[TaskHistoryFilters] = None,
    ) -> List[TaskHistorySchema]:
        """Получить историю изменений задачи с фильтрацией."""
        query_filters = [self._collection.task_id == task_id]

        if filters:
            if filters.change_type:
                query_filters.append(self._collection.change_type == filters.change_type)
            if filters.changed_at_gte:
                query_filters.append(self._collection.changed_at >= filters.changed_at_gte)
            if filters.changed_at_lte:
                query_filters.append(self._collection.changed_at <= filters.changed_at_lte)

        query = (
            select(self._collection)
            .where(and_(*query_filters))
            .order_by(self._collection.changed_at.desc())
        )

        result = await session.scalars(query)
        return [TaskHistorySchema.model_validate(row) for row in result.all()]
