from datetime import datetime
from datetime import timedelta
from typing import Type

from sqlalchemy import and_, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.core.exceptions.tasks import TaskNotFoundException
from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.models import Task
from task_service.schemas.task import CreateTask, TaskFilters, TaskSchema, TaskStatus, UpdateTask

logger = get_logger(__name__)


class TaskRepository:
    """Репозиторий для работы с задачами."""

    _tasks_collection: Type[Task] = Task

    @log(logger)
    async def get_one_task(
        self,
        session: AsyncSession,
        task_id: int,
    ) -> TaskSchema:
        query = select(self._tasks_collection).where(self._tasks_collection.id == task_id)
        db_row = await session.scalar(query)
        if not db_row:
            raise TaskNotFoundException(task_id)
        return TaskSchema.model_validate(db_row)

    @log(logger)
    async def get_all_tasks(
        self,
        session: AsyncSession,
        filters: TaskFilters,
    ) -> tuple[list[TaskSchema], int]:
        query_filters = self._build_filters(filters)

        query = (
            select(self._tasks_collection)
            .where(and_(*query_filters))
            .limit(filters.limit)
            .offset(filters.offset)
            .order_by(self._tasks_collection.created_at.desc())
        )

        db_rows = await session.scalars(query)

        count_query = select(func.count(self._tasks_collection.id.distinct())).where(and_(*query_filters))
        total = await session.scalar(count_query)

        #list comprehension
        return [TaskSchema.model_validate(obj=obj) for obj in db_rows.all()], total or 0

    @log(logger)
    async def create_task(
        self,
        session: AsyncSession,
        task: CreateTask,
    ) -> TaskSchema:
        values = task.model_dump()
        query = insert(self._tasks_collection).values(values).returning(self._tasks_collection)
        result = await session.scalar(query)
        await session.flush()
        return TaskSchema.model_validate(result)

    @log(logger)
    async def update_task(
        self,
        session: AsyncSession,
        task_id: int,
        task: UpdateTask,
    ) -> TaskSchema:
        values = task.model_dump(exclude_unset=True, exclude_none=True)
        values["updated_at"] = datetime.utcnow()

        query = (
            update(self._tasks_collection)
            .where(self._tasks_collection.id == task_id)
            .values(values)
            .returning(self._tasks_collection)
        )

        result = await session.scalar(query)

        if result is None:
            raise TaskNotFoundException(task_id)

        await session.flush()

        return TaskSchema.model_validate(result)

    @log(logger)
    async def delete_task(
        self,
        session: AsyncSession,
        task_id: int,
    ) -> None:
        query = delete(self._tasks_collection).where(self._tasks_collection.id == task_id)

        result = await session.execute(query)

        if result.rowcount == 0:
            raise TaskNotFoundException(task_id)

        await session.flush()

    @log(logger)
    async def get_tasks_for_auto_escalation(
        self,
        session: AsyncSession,
        *,
        older_than_days: int,
        limit: int = 500,
    ) -> list[TaskSchema]:
        """
        Получить задачи, которые слишком долго находятся в TODO.

        Так как отдельного "updated_at статуса" нет, используем `created_at`:
        если задача всё ещё TODO и создана давно — она "залежалась" и может быть повышена.
        """
        threshold = datetime.utcnow() - timedelta(days=older_than_days)

        query = (
            select(self._tasks_collection)
            .where(
                and_(
                    self._tasks_collection.status == TaskStatus.TODO,
                    self._tasks_collection.created_at <= threshold,
                )
            )
            .order_by(self._tasks_collection.created_at.asc())
            .limit(limit)
        )

        db_rows = await session.scalars(query)
        return [TaskSchema.model_validate(obj=obj) for obj in db_rows.all()]

    def _build_filters(self, filters: TaskFilters) -> list:
        """Построить фильтры для запроса."""
        filters_list = []

        if filters.search:
            search_pattern = f"%{filters.search}%"
            # Search only in title (case-insensitive) for substring match
            filters_list.append(self._tasks_collection.title.ilike(search_pattern))

        if filters.status:
            filters_list.append(self._tasks_collection.status == filters.status)

        if filters.priority:
            filters_list.append(self._tasks_collection.priority == filters.priority)

        if filters.assignee:
            filters_list.append(self._tasks_collection.assignee == filters.assignee)

        if filters.created_by:
            filters_list.append(self._tasks_collection.created_by == filters.created_by)

        if filters.created_at_gte:
            filters_list.append(self._tasks_collection.created_at >= filters.created_at_gte)

        if filters.created_at_lte:
            filters_list.append(self._tasks_collection.created_at <= filters.created_at_lte)

        return filters_list

    @log(logger)
    async def get_total_tasks_count(self, session: AsyncSession) -> int:
        query = select(func.count()).select_from(self._tasks_collection)
        result = await session.scalar(query)
        return result or 0

    @log(logger)
    async def get_tasks_count_by_status(self, session: AsyncSession) -> dict[str, int]:
        query = (
            select(self._tasks_collection.status, func.count(self._tasks_collection.id))
            .group_by(self._tasks_collection.status)
        )
        result = await session.execute(query)
        return {row[0]: row[1] for row in result.fetchall()}

    @log(logger)
    async def get_tasks_count_by_priority(self, session: AsyncSession) -> dict[str, int]:
        query = (
            select(self._tasks_collection.priority, func.count(self._tasks_collection.id))
            .group_by(self._tasks_collection.priority)
        )
        result = await session.execute(query)
        return {row[0]: row[1] for row in result.fetchall()}

    @log(logger)
    async def get_tasks_count_by_assignee(self, session: AsyncSession) -> dict[str, int]:
        query = (
            select(self._tasks_collection.assignee, func.count(self._tasks_collection.id))
            .where(self._tasks_collection.assignee.isnot(None))
            .group_by(self._tasks_collection.assignee)
        )
        result = await session.execute(query)
        return {row[0]: row[1] for row in result.fetchall()}
