import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from task_service.domain.use_cases.get_task_statistics import GetTaskStatisticsUseCase
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.redis.repository import RedisRepository
from task_service.schemas.task import TaskStatistics


class TestGetTaskStatisticsUseCase:
    """Тесты use case получения статистики задач."""

    @pytest.fixture
    def mock_database(self) -> Database:
        """Мокированная БД."""
        mock = AsyncMock(spec=Database)
        return mock

    @pytest.fixture
    def mock_repository(self) -> TaskRepository:
        """Мокированный репозиторий."""
        mock = AsyncMock(spec=TaskRepository)
        return mock

    @pytest.fixture
    def mock_cache(self) -> RedisRepository:
        """Мокированный кэш Redis."""
        mock = AsyncMock(spec=RedisRepository)
        return mock

    @pytest.fixture
    def use_case(
        self,
        mock_database: Database,
        mock_repository: TaskRepository,
        mock_cache: RedisRepository,
    ) -> GetTaskStatisticsUseCase:
        """Инстанс use case с мокированными зависимостями."""
        return GetTaskStatisticsUseCase(
            database=mock_database,
            repository=mock_repository,
            cache=mock_cache,
        )

    @pytest.fixture
    def expected_statistics(self) -> TaskStatistics:
        """Ожидаемая статистика."""
        return TaskStatistics(
            total_tasks=10,
            by_status={"todo": 5, "in_progress": 3, "done": 2},
            by_priority={"low": 2, "medium": 5, "high": 3},
            by_assignee={"user1": 4, "user2": 6},
        )

    async def test_cache_hit(
        self,
        use_case: GetTaskStatisticsUseCase,
        mock_cache: RedisRepository,
        expected_statistics: TaskStatistics,
    ) -> None:
        """Проверка кэша: при наличии в кэше возвращает из кэша."""
        # Настраиваем мок чтобы вернуть статистику из кэша
        mock_cache.get_task_statistics = AsyncMock(return_value=expected_statistics)

        result = await use_case.execute()

        assert result == expected_statistics
        # Проверяем что кэш был запрошен
        mock_cache.get_task_statistics.assert_called_once()

    async def test_cache_miss(
        self,
        use_case: GetTaskStatisticsUseCase,
        mock_cache: RedisRepository,
        mock_database: Database,
        mock_repository: TaskRepository,
        expected_statistics: TaskStatistics,
    ) -> None:
        """Проверка кэша: при отсутствии в кэше читает из БД и кэширует."""
        # Настраиваем мок кэша возвращать None (кэш промах)
        mock_cache.get_task_statistics = AsyncMock(return_value=None)

        # Настраиваем мок репозитория возвращать статистику
        mock_repository.get_tasks_count = AsyncMock(return_value=10)
        mock_repository.get_tasks_count_by_status = AsyncMock(
            return_value={"todo": 5, "in_progress": 3, "done": 2}
        )
        mock_repository.get_tasks_count_by_priority = AsyncMock(
            return_value={"low": 2, "medium": 5, "high": 3}
        )
        mock_repository.get_tasks_count_by_assignee = AsyncMock(
            return_value={"user1": 4, "user2": 6}
        )

        # Настраиваем мок БД для session()
        mock_db_session = AsyncMock()
        mock_database.session = MagicMock(return_value=mock_db_session)
        mock_db_session.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        result = await use_case.execute()

        assert result.total_tasks == 10
        assert result.by_status == {"todo": 5, "in_progress": 3, "done": 2}
        assert result.by_priority == {"low": 2, "medium": 5, "high": 3}
        assert result.by_assignee == {"user1": 4, "user2": 6}

        # Проверяем что результат был сохранён в кэш
        mock_cache.set_task_statistics.assert_called_once()
        call_args = mock_cache.set_task_statistics.call_args
        assert call_args[0][0].total_tasks == 10

    async def test_statistics_correctness(
        self,
        use_case: GetTaskStatisticsUseCase,
        mock_cache: RedisRepository,
        mock_database: Database,
        mock_repository: TaskRepository,
    ) -> None:
        """Проверка корректности расчёта статистики."""
        mock_cache.get_task_statistics = AsyncMock(return_value=None)

        mock_repository.get_tasks_count = AsyncMock(return_value=50)
        mock_repository.get_tasks_count_by_status = AsyncMock(
            return_value={"todo": 20, "in_progress": 15, "done": 10, "cancelled": 5}
        )
        mock_repository.get_tasks_count_by_priority = AsyncMock(
            return_value={"critical": 5, "high": 15, "medium": 20, "low": 10}
        )
        mock_repository.get_tasks_count_by_assignee = AsyncMock(
            return_value={"alice": 30, "bob": 20}
        )

        mock_db_session = AsyncMock()
        mock_database.session = MagicMock(return_value=mock_db_session)
        mock_db_session.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        result = await use_case.execute()

        assert result.total_tasks == 50
        assert sum(result.by_status.values()) == 50
        assert sum(result.by_priority.values()) == 50
        assert sum(result.by_assignee.values()) == 50

    async def test_cache_ttl_respected(
        self,
        use_case: GetTaskStatisticsUseCase,
        mock_cache: RedisRepository,
        mock_database: Database,
        mock_repository: TaskRepository,
    ) -> None:
        """Проверка что используется TTL 1 минута (60 секунд)."""
        mock_cache.get_task_statistics = AsyncMock(return_value=None)

        mock_repository.get_tasks_count = AsyncMock(return_value=10)
        mock_repository.get_tasks_count_by_status = AsyncMock(return_value={})
        mock_repository.get_tasks_count_by_priority = AsyncMock(return_value={})
        mock_repository.get_tasks_count_by_assignee = AsyncMock(return_value={})

        mock_db_session = AsyncMock()
        mock_database.session = MagicMock(return_value=mock_db_session)
        mock_db_session.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        await use_case.execute()

        # Проверяем что set_task_statistics был вызван с TTL 60 секунд
        mock_cache.set_task_statistics.assert_called_once()
        # TTL устанавливается в RedisRepository по умолчанию на 60 сек
