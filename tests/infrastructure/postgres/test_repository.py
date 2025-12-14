import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.core.exceptions.tasks import TaskNotFoundException
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.schemas.task import CreateTask, TaskFilters, TaskSchema, TaskStatus, TaskPriority, UpdateTask


class TestTaskRepository:
    """Тесты репозитория задач."""

    async def test_create_task(
        self,
        async_session: AsyncSession,
        task_repository: TaskRepository,
        valid_create_task: CreateTask,
    ) -> None:
        """Создание задачи в БД."""
        result = await task_repository.create_task(
            session=async_session,
            task=valid_create_task,
        )

        assert isinstance(result, TaskSchema)
        assert result.id is not None
        assert result.title == valid_create_task.title
        assert result.status == valid_create_task.status

    async def test_get_one_task(
        self,
        async_session: AsyncSession,
        task_repository: TaskRepository,
        valid_create_task: CreateTask,
    ) -> None:
        """Получение задачи по ID."""
        # Создаём задачу
        created = await task_repository.create_task(
            session=async_session,
            task=valid_create_task,
        )

        # Получаем
        result = await task_repository.get_one_task(
            session=async_session,
            task_id=created.id,
        )

        assert result.id == created.id
        assert result.title == created.title

    async def test_get_one_task_not_found(
        self,
        async_session: AsyncSession,
        task_repository: TaskRepository,
    ) -> None:
        """Задача не найдена."""
        with pytest.raises(TaskNotFoundException):
            await task_repository.get_one_task(
                session=async_session,
                task_id=99999,
            )

    async def test_get_all_tasks(
        self,
        async_session: AsyncSession,
        task_repository: TaskRepository,
        valid_create_task: CreateTask,
    ) -> None:
        """Получение списка задач."""
        # Создаём задачу
        await task_repository.create_task(
            session=async_session,
            task=valid_create_task,
        )

        filters = TaskFilters(limit=10, offset=0)
        tasks, total = await task_repository.get_all_tasks(
            session=async_session,
            filters=filters,
        )

        assert len(tasks) >= 1
        assert total >= 1

    async def test_get_all_tasks_with_status_filter(
        self,
        async_session: AsyncSession,
        task_repository: TaskRepository,
        valid_create_task: CreateTask,
    ) -> None:
        """Фильтрация задач по статусу."""
        # Создаём задачу со статусом TODO
        await task_repository.create_task(
            session=async_session,
            task=valid_create_task,
        )

        filters = TaskFilters(limit=10, offset=0, status=TaskStatus.TODO)
        tasks, total = await task_repository.get_all_tasks(
            session=async_session,
            filters=filters,
        )

        for task in tasks:
            assert task.status == TaskStatus.TODO

    async def test_update_task(
        self,
        async_session: AsyncSession,
        task_repository: TaskRepository,
        valid_create_task: CreateTask,
    ) -> None:
        """Обновление задачи."""
        # Создаём
        created = await task_repository.create_task(
            session=async_session,
            task=valid_create_task,
        )

        # Обновляем
        update_data = UpdateTask(status=TaskStatus.IN_PROGRESS)
        updated = await task_repository.update_task(
            session=async_session,
            task_id=created.id,
            task=update_data,
        )

        assert updated.id == created.id
        assert updated.status == TaskStatus.IN_PROGRESS

    async def test_delete_task(
        self,
        async_session: AsyncSession,
        task_repository: TaskRepository,
        valid_create_task: CreateTask,
    ) -> None:
        """Удаление задачи."""
        # Создаём
        created = await task_repository.create_task(
            session=async_session,
            task=valid_create_task,
        )

        # Удаляем
        await task_repository.delete_task(
            session=async_session,
            task_id=created.id,
        )

        # Проверяем что удалена
        with pytest.raises(TaskNotFoundException):
            await task_repository.get_one_task(
                session=async_session,
                task_id=created.id,
            )

    async def test_delete_task_not_found(
        self,
        async_session: AsyncSession,
        task_repository: TaskRepository,
    ) -> None:
        """Удаление несуществующей задачи."""
        with pytest.raises(TaskNotFoundException):
            await task_repository.delete_task(
                session=async_session,
                task_id=99999,
            )

