import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from task_service.domain.use_cases.create_task import CreateTaskUseCase
from task_service.domain.use_cases.update_task import UpdateTaskUseCase
from task_service.domain.use_cases.delete_task import DeleteTaskUseCase
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from task_service.infrastructure.redis.repository import RedisRepository
from task_service.infrastructure.kafka.publisher import KafkaPublisher
from task_service.schemas.task import (
    CreateTask,
    UpdateTask,
    TaskSchema,
    TaskStatus,
    TaskPriority,
)


class TestCacheInvalidation:
    """Тесты инвалидации кэша статистики при изменении задач."""

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
    def mock_publisher(self) -> RabbitMQPublisher:
        """Мокированный RabbitMQ publisher."""
        mock = AsyncMock(spec=RabbitMQPublisher)
        return mock

    @pytest.fixture
    def mock_cache(self) -> RedisRepository:
        """Мокированный кэш Redis."""
        mock = AsyncMock(spec=RedisRepository)
        return mock

    @pytest.fixture
    def mock_kafka_publisher(self) -> KafkaPublisher:
        """Мокированный Kafka publisher."""
        mock = AsyncMock(spec=KafkaPublisher)
        return mock

    @pytest.fixture
    def test_task_schema(self) -> TaskSchema:
        """Тестовая задача."""
        now = datetime.now(timezone.utc)
        return TaskSchema(
            id=1,
            title="Test Task",
            description="Test Description",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            assignee="user1",
            due_date=None,
            created_by="test_user",
            created_at=now,
            updated_at=now,
        )

    async def test_create_task_invalidates_statistics_cache(
        self,
        mock_database: Database,
        mock_repository: TaskRepository,
        mock_publisher: RabbitMQPublisher,
        mock_cache: RedisRepository,
        mock_kafka_publisher: KafkaPublisher,
        test_task_schema: TaskSchema,
    ) -> None:
        """Проверка что создание задачи инвалидирует кэш статистики."""
        use_case = CreateTaskUseCase(
            database=mock_database,
            repository=mock_repository,
            publisher=mock_publisher,
            cache=mock_cache,
            kafka_publisher=mock_kafka_publisher,
        )

        create_task = CreateTask(
            title="New Task",
            description="New Description",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            created_by="test_user",
        )

        # Настраиваем мокированную БД
        mock_db_session = AsyncMock()
        mock_database.session = MagicMock(return_value=mock_db_session)
        mock_db_session.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        # Настраиваем мокированный репозиторий
        mock_repository.create_task = AsyncMock(return_value=test_task_schema)
        mock_publisher.publish_task_notification = AsyncMock()
        mock_kafka_publisher.publish_task_event = AsyncMock()
        mock_cache.delete_task_statistics = AsyncMock()

        await use_case.execute(create_task)

        # Проверяем что кэш статистики был инвалидирован
        mock_cache.delete_task_statistics.assert_called_once()

    async def test_update_task_invalidates_statistics_cache(
        self,
        mock_database: Database,
        mock_repository: TaskRepository,
        mock_publisher: RabbitMQPublisher,
        mock_cache: RedisRepository,
        mock_kafka_publisher: KafkaPublisher,
        test_task_schema: TaskSchema,
    ) -> None:
        """Проверка что обновление задачи инвалидирует кэш статистики."""
        use_case = UpdateTaskUseCase(
            database=mock_database,
            repository=mock_repository,
            publisher=mock_publisher,
            cache=mock_cache,
            kafka_publisher=mock_kafka_publisher,
        )

        update_task = UpdateTask(
            title="Updated Task",
            status=TaskStatus.IN_PROGRESS,
        )

        # Настраиваем мокированную БД
        mock_db_session = AsyncMock()
        mock_database.session = MagicMock(return_value=mock_db_session)
        mock_db_session.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        # Настраиваем мокированный репозиторий
        mock_repository.get_one_task = AsyncMock(return_value=test_task_schema)
        mock_repository.update_task = AsyncMock(return_value=test_task_schema)
        mock_publisher.publish_task_notification = AsyncMock()
        mock_kafka_publisher.publish_task_event = AsyncMock()
        mock_cache.delete_task = AsyncMock()
        mock_cache.set_task = AsyncMock()
        mock_cache.delete_task_statistics = AsyncMock()

        await use_case.execute(update_task, task_id=1, updated_by="test_user")

        # Проверяем что кэш статистики был инвалидирован
        mock_cache.delete_task_statistics.assert_called_once()

    async def test_delete_task_invalidates_statistics_cache(
        self,
        mock_database: Database,
        mock_repository: TaskRepository,
        mock_publisher: RabbitMQPublisher,
        mock_cache: RedisRepository,
        mock_kafka_publisher: KafkaPublisher,
        test_task_schema: TaskSchema,
    ) -> None:
        """Проверка что удаление задачи инвалидирует кэш статистики."""
        use_case = DeleteTaskUseCase(
            database=mock_database,
            repository=mock_repository,
            cache=mock_cache,
            kafka_publisher=mock_kafka_publisher,
        )

        # Настраиваем мокированную БД
        mock_db_session = AsyncMock()
        mock_database.session = MagicMock(return_value=mock_db_session)
        mock_db_session.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_db_session.__aexit__ = AsyncMock(return_value=None)

        # Настраиваем мокированный репозиторий
        mock_repository.get_one_task = AsyncMock(return_value=test_task_schema)
        mock_repository.delete_task = AsyncMock()
        mock_kafka_publisher.publish_task_event = AsyncMock()
        mock_cache.delete_task = AsyncMock()
        mock_cache.delete_task_statistics = AsyncMock()

        await use_case.execute(task_id=1)

        # Проверяем что кэш статистики был инвалидирован
        mock_cache.delete_task_statistics.assert_called_once()
