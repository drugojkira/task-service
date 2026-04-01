from __future__ import annotations

from io import StringIO

from aiocsv import AsyncWriter

from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.schemas.task import TaskFilters, TaskSchema

logger = get_logger(__name__)


class _AsyncStringIO:
    """Async adapter around StringIO for aiocsv."""

    def __init__(self) -> None:
        self._buf = StringIO()

    async def write(self, data: str) -> int:
        return self._buf.write(data)

    def getvalue(self) -> str:
        return self._buf.getvalue()


class ExportTasksToCSVUseCase:
    """Export tasks to CSV in-memory."""

    def __init__(self, database: Database, repository: TaskRepository) -> None:
        self._database = database
        self._repository = repository

    @staticmethod
    def _row(task: TaskSchema) -> list[str]:
        return [
            str(task.id),
            task.title,
            task.status.value,
            task.priority.value,
            task.assignee or "",
            task.created_at.isoformat(),
            task.updated_at.isoformat(),
        ]

    @log(logger)
    async def execute(self, *, filters: TaskFilters) -> bytes:
        # Export is expected to return a file; ignore pagination by exporting from offset 0.
        export_filters = filters.model_copy(update={"offset": 0, "limit": max(filters.limit, 10_000)})

        async with self._database.session() as session:
            tasks, _total = await self._repository.get_all_tasks(session=session, filters=export_filters)

        out = _AsyncStringIO()
        writer = AsyncWriter(out)

        await writer.writerow(["id", "title", "status", "priority", "assignee", "created_at", "updated_at"])
        for task in tasks:
            await writer.writerow(self._row(task))

        return out.getvalue().encode("utf-8")

