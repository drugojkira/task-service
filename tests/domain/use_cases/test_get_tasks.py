import pytest

from task_service.core.exceptions.tasks import TaskNotFoundException
from task_service.domain.use_cases.get_tasks import GetTasksUseCase
from task_service.schemas.task import TaskFilters, TaskSchema
from tests.helpers import TestDatabaseSessionWrapper
from tests.mocks import MockedTaskRepository, MockedRedisRepository


class TestGetTasksUseCase:
    """Тесты use case получения задач."""

    async def test_get_all_tasks_success(
        self,
        valid_task_schema: TaskSchema,
        valid_task_filters: TaskFilters,
        db_with_active_session: TestDatabaseSessionWrapper,
    ) -> None:
        """Успешное получение списка задач."""
        mocked_repo = MockedTaskRepository(to_return=valid_task_schema)
        mocked_cache = MockedRedisRepository()

        use_case = GetTasksUseCase(
            database=db_with_active_session,
            repository=mocked_repo,
            cache=mocked_cache,
        )

        tasks, total = await use_case.execute(filters=valid_task_filters)

        assert len(tasks) == 1
        assert total == 1
        assert mocked_repo.calls_counter["get_all_tasks"] == 1

    async def test_get_all_tasks_empty(
        self,
        valid_task_filters: TaskFilters,
        db_with_active_session: TestDatabaseSessionWrapper,
    ) -> None:
        """Получение пустого списка задач."""
        mocked_repo = MockedTaskRepository(to_return=None)
        mocked_cache = MockedRedisRepository()

        use_case = GetTasksUseCase(
            database=db_with_active_session,
            repository=mocked_repo,
            cache=mocked_cache,
        )

        tasks, total = await use_case.execute(filters=valid_task_filters)

        assert tasks == []
        assert total == 0

    async def test_get_task_by_id_cache_hit(
        self,
        valid_task_schema: TaskSchema,
        db_with_active_session: TestDatabaseSessionWrapper,
    ) -> None:
        """Получение задачи из кэша (cache hit)."""
        mocked_repo = MockedTaskRepository(to_return=valid_task_schema)
        mocked_cache = MockedRedisRepository()

        # Предварительно кладём в кэш
        await mocked_cache.set_task(valid_task_schema)

        use_case = GetTasksUseCase(
            database=db_with_active_session,
            repository=mocked_repo,
            cache=mocked_cache,
        )

        result = await use_case.get_by_id(task_id=valid_task_schema.id)

        assert result.id == valid_task_schema.id
        # Репозиторий НЕ вызывался - взяли из кэша
        assert mocked_repo.calls_counter["get_one_task"] == 0
        assert mocked_cache.calls_counter["get_task"] == 1

    async def test_get_task_by_id_cache_miss(
        self,
        valid_task_schema: TaskSchema,
        db_with_active_session: TestDatabaseSessionWrapper,
    ) -> None:
        """Получение задачи из БД при отсутствии в кэше (cache miss)."""
        mocked_repo = MockedTaskRepository(to_return=valid_task_schema)
        mocked_cache = MockedRedisRepository()

        use_case = GetTasksUseCase(
            database=db_with_active_session,
            repository=mocked_repo,
            cache=mocked_cache,
        )

        result = await use_case.get_by_id(task_id=valid_task_schema.id)

        assert result.id == valid_task_schema.id
        # Репозиторий вызвался
        assert mocked_repo.calls_counter["get_one_task"] == 1
        # Результат закэширован
        assert mocked_cache.calls_counter["set_task"] == 1

    async def test_get_task_by_id_not_found(
        self,
        db_with_active_session: TestDatabaseSessionWrapper,
    ) -> None:
        """Задача не найдена."""
        mocked_repo = MockedTaskRepository(to_raise=TaskNotFoundException(task_id=999))
        mocked_cache = MockedRedisRepository()

        use_case = GetTasksUseCase(
            database=db_with_active_session,
            repository=mocked_repo,
            cache=mocked_cache,
        )

        with pytest.raises(TaskNotFoundException):
            await use_case.get_by_id(task_id=999)



