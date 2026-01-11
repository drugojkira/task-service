import pytest

from task_service.domain.use_cases.create_task import CreateTaskUseCase
from task_service.schemas.task import CreateTask, TaskSchema
from tests.helpers import TestDatabaseSessionWrapper
from tests.mocks import MockedTaskRepository, MockedRedisRepository, MockedRabbitMQPublisher


class TestCreateTaskUseCase:
    """Тесты use case создания задачи."""

    async def test_create_task_success(
        self,
        valid_create_task: CreateTask,
        valid_task_schema: TaskSchema,
        db_with_active_session: TestDatabaseSessionWrapper,
    ) -> None:
        """Успешное создание задачи."""
        mocked_repo = MockedTaskRepository(to_return=valid_task_schema)
        mocked_cache = MockedRedisRepository()
        mocked_publisher = MockedRabbitMQPublisher()

        use_case = CreateTaskUseCase(
            database=db_with_active_session,
            repository=mocked_repo,
            publisher=mocked_publisher,
            cache=mocked_cache,
        )

        result = await use_case.execute(task=valid_create_task)

        assert isinstance(result, TaskSchema)
        assert result.id == valid_task_schema.id
        assert result.title == valid_task_schema.title
        assert mocked_repo.calls_counter["create_task"] == 1
        assert mocked_cache.calls_counter["set_task"] == 1
        assert mocked_publisher.calls_counter["publish_task_notification"] == 1

    async def test_create_task_publishes_notification(
        self,
        valid_create_task: CreateTask,
        valid_task_schema: TaskSchema,
        db_with_active_session: TestDatabaseSessionWrapper,
    ) -> None:
        """Проверка что при создании отправляется уведомление."""
        mocked_repo = MockedTaskRepository(to_return=valid_task_schema)
        mocked_cache = MockedRedisRepository()
        mocked_publisher = MockedRabbitMQPublisher()

        use_case = CreateTaskUseCase(
            database=db_with_active_session,
            repository=mocked_repo,
            publisher=mocked_publisher,
            cache=mocked_cache,
        )

        await use_case.execute(task=valid_create_task)

        assert len(mocked_publisher.published_messages) == 1
        notification = mocked_publisher.published_messages[0]
        assert notification.task_id == valid_task_schema.id
        assert notification.event_type.value == "created"

    async def test_create_task_caches_result(
        self,
        valid_create_task: CreateTask,
        valid_task_schema: TaskSchema,
        db_with_active_session: TestDatabaseSessionWrapper,
    ) -> None:
        """Проверка что созданная задача кэшируется."""
        mocked_repo = MockedTaskRepository(to_return=valid_task_schema)
        mocked_cache = MockedRedisRepository()
        mocked_publisher = MockedRabbitMQPublisher()

        use_case = CreateTaskUseCase(
            database=db_with_active_session,
            repository=mocked_repo,
            publisher=mocked_publisher,
            cache=mocked_cache,
        )

        await use_case.execute(task=valid_create_task)

        # Проверяем что задача в кэше
        cached_task = await mocked_cache.get_task(valid_task_schema.id)
        assert cached_task is not None
        assert cached_task.id == valid_task_schema.id



