import pytest
from dishka import Provider, Scope
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status
from unittest.mock import AsyncMock

from task_service.core.exceptions.tasks import TaskNotFoundException
from task_service.domain.use_cases.create_task import CreateTaskUseCase
from task_service.domain.use_cases.get_tasks import GetTasksUseCase
from task_service.domain.use_cases.get_task_statistics import GetTaskStatisticsUseCase
from task_service.schemas.task import TaskSchema, TaskStatistics
from tests.conftest import override
from tests.mocks import MockedUseCase


class TestTasksAPI:
    """Тесты API задач."""

    # === GET /api/v1/tasks ===

    async def test_get_all_tasks_success(
        self,
        app: FastAPI,
        test_client: AsyncClient,
        valid_task_schema: TaskSchema,
    ) -> None:
        """Успешное получение списка задач."""
        mocked_use_case = MockedUseCase(to_return=([valid_task_schema], 1))

        # Переопределяем execute чтобы возвращал tuple
        async def mock_execute(*args, **kwargs):
            return [valid_task_schema], 1

        mocked_use_case.execute = mock_execute

        mock_provider = Provider(scope=Scope.REQUEST)
        mock_provider.provide(lambda: mocked_use_case, provides=GetTasksUseCase)

        async with override(app.state.dishka_container, mock_provider):
            response = await test_client.get("/api/v1/tasks")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data

    # === GET /api/v1/tasks/{task_id} ===

    async def test_get_task_by_id_success(
        self,
        app: FastAPI,
        test_client: AsyncClient,
        valid_task_schema: TaskSchema,
    ) -> None:
        """Успешное получение задачи по ID."""
        mocked_use_case = MockedUseCase(to_return=valid_task_schema)

        mock_provider = Provider(scope=Scope.REQUEST)
        mock_provider.provide(lambda: mocked_use_case, provides=GetTasksUseCase)

        async with override(app.state.dishka_container, mock_provider):
            response = await test_client.get("/api/v1/tasks/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == valid_task_schema.id

    async def test_get_task_by_id_not_found(
        self,
        app: FastAPI,
        test_client: AsyncClient,
    ) -> None:
        """Задача не найдена - 404."""
        mocked_use_case = MockedUseCase(to_raise=TaskNotFoundException(task_id=999))

        mock_provider = Provider(scope=Scope.REQUEST)
        mock_provider.provide(lambda: mocked_use_case, provides=GetTasksUseCase)

        async with override(app.state.dishka_container, mock_provider):
            response = await test_client.get("/api/v1/tasks/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # === POST /api/v1/tasks ===

    async def test_create_task_success(
        self,
        app: FastAPI,
        test_client: AsyncClient,
        valid_task_schema: TaskSchema,
    ) -> None:
        """Успешное создание задачи."""
        mocked_use_case = MockedUseCase(to_return=valid_task_schema)

        mock_provider = Provider(scope=Scope.REQUEST)
        mock_provider.provide(lambda: mocked_use_case, provides=CreateTaskUseCase)

        payload = {
            "title": "New Task",
            "description": "Description",
            "priority": "medium",
        }

        async with override(app.state.dishka_container, mock_provider):
            response = await test_client.post(
                "/api/v1/tasks",
                json=payload,
                headers={"X-User-Name": "test_user"},
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == valid_task_schema.id

    async def test_create_task_validation_error(
        self,
        app: FastAPI,
        test_client: AsyncClient,
    ) -> None:
        """Ошибка валидации - пустой title."""
        payload = {
            "title": "",  # пустой
            "priority": "medium",
        }

        response = await test_client.post(
            "/api/v1/tasks",
            json=payload,
            headers={"X-User-Name": "test_user"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # === GET /api/v1/tasks/statistics ===

    async def test_get_task_statistics_success(
        self,
        app: FastAPI,
        test_client: AsyncClient,
    ) -> None:
        """Успешное получение статистики задач."""
        expected_stats = TaskStatistics(
            total_tasks=10,
            by_status={"todo": 5, "in_progress": 3, "done": 2},
            by_priority={"low": 2, "medium": 5, "high": 3},
            by_assignee={"user1": 4, "user2": 6},
        )

        mocked_use_case = MockedUseCase(to_return=expected_stats)
        mocked_use_case.execute = AsyncMock(return_value=expected_stats)

        mock_provider = Provider(scope=Scope.REQUEST)
        mock_provider.provide(lambda: mocked_use_case, provides=GetTaskStatisticsUseCase)

        async with override(app.state.dishka_container, mock_provider):
            response = await test_client.get("/api/v1/tasks/statistics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_tasks"] == 10
        assert data["by_status"] == {"todo": 5, "in_progress": 3, "done": 2}
        assert data["by_priority"] == {"low": 2, "medium": 5, "high": 3}
        assert data["by_assignee"] == {"user1": 4, "user2": 6}

    async def test_get_task_statistics_empty(
        self,
        app: FastAPI,
        test_client: AsyncClient,
    ) -> None:
        """Получение статистики когда нет задач."""
        expected_stats = TaskStatistics(
            total_tasks=0,
            by_status={},
            by_priority={},
            by_assignee={},
        )

        mocked_use_case = MockedUseCase(to_return=expected_stats)
        mocked_use_case.execute = AsyncMock(return_value=expected_stats)

        mock_provider = Provider(scope=Scope.REQUEST)
        mock_provider.provide(lambda: mocked_use_case, provides=GetTaskStatisticsUseCase)

        async with override(app.state.dishka_container, mock_provider):
            response = await test_client.get("/api/v1/tasks/statistics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_tasks"] == 0
        assert data["by_status"] == {}
        assert data["by_priority"] == {}
        assert data["by_assignee"] == {}



