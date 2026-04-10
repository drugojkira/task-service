from typing import List

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.models import TaskAssignee

logger = get_logger(__name__)


class AssigneeRepository:
    """Репозиторий для работы с исполнителями задач."""

    _collection = TaskAssignee

    @log(logger)
    async def set_assignees(
        self,
        session: AsyncSession,
        task_id: int,
        assignee_emails: List[str],
    ) -> List[str]:
        """Установить список исполнителей задачи (заменяет существующих)."""
        # Удаляем текущих
        await session.execute(
            delete(self._collection).where(self._collection.task_id == task_id)
        )

        if not assignee_emails:
            await session.flush()
            return []

        # Добавляем новых
        values = [
            {"task_id": task_id, "assignee_email": email}
            for email in assignee_emails
        ]
        await session.execute(insert(self._collection), values)
        await session.flush()
        return assignee_emails

    @log(logger)
    async def get_by_task_id(
        self,
        session: AsyncSession,
        task_id: int,
    ) -> List[str]:
        """Получить список исполнителей задачи."""
        query = (
            select(self._collection.assignee_email)
            .where(self._collection.task_id == task_id)
            .order_by(self._collection.assigned_at.asc())
        )
        result = await session.scalars(query)
        return list(result.all())
