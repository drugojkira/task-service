from collections import defaultdict
from typing import Any


class MockedTaskRepository:
    """Мок репозитория задач для тестирования use cases."""

    calls_counter: dict[str, int]

    def __init__(
        self,
        to_return: Any | None = None,
        to_raise: Exception | None = None,
    ) -> None:
        self._to_return = to_return
        self._to_raise = to_raise
        self.calls_counter = defaultdict(int)

    def _add_counter_and_check_to_raise(self, function_name: str) -> None:
        self.calls_counter[function_name] += 1
        if self._to_raise:
            raise self._to_raise

    async def create_task(self, *args: Any, **kwargs: Any) -> Any | None:
        self._add_counter_and_check_to_raise("create_task")
        return self._to_return

    async def get_one_task(self, *args: Any, **kwargs: Any) -> Any | None:
        self._add_counter_and_check_to_raise("get_one_task")
        return self._to_return

    async def get_all_tasks(self, *args: Any, **kwargs: Any) -> tuple[list, int]:
        self._add_counter_and_check_to_raise("get_all_tasks")
        if self._to_return:
            return [self._to_return], 1
        return [], 0

    async def update_task(self, *args: Any, **kwargs: Any) -> Any | None:
        self._add_counter_and_check_to_raise("update_task")
        return self._to_return

    async def delete_task(self, *args: Any, **kwargs: Any) -> None:
        self._add_counter_and_check_to_raise("delete_task")


class MockedRedisRepository:
    """Мок Redis репозитория."""

    calls_counter: dict[str, int]

    def __init__(self) -> None:
        self.calls_counter = defaultdict(int)
        self._cache: dict[int, Any] = {}

    async def get_task(self, task_id: int) -> Any | None:
        self.calls_counter["get_task"] += 1
        return self._cache.get(task_id)

    async def set_task(self, task: Any, ex: int | None = None) -> None:
        self.calls_counter["set_task"] += 1
        self._cache[task.id] = task

    async def delete_task(self, task_id: int) -> None:
        self.calls_counter["delete_task"] += 1
        self._cache.pop(task_id, None)


class MockedRabbitMQPublisher:
    """Мок RabbitMQ publisher."""

    calls_counter: dict[str, int]

    def __init__(self) -> None:
        self.calls_counter = defaultdict(int)
        self.published_messages: list = []

    async def publish_task_notification(self, message: Any) -> None:
        self.calls_counter["publish_task_notification"] += 1
        self.published_messages.append(message)


class MockedUseCase:
    """Мок use case для тестирования API."""

    def __init__(
        self,
        to_return: Any | None = None,
        to_raise: Exception | None = None,
    ) -> None:
        self._to_return = to_return
        self._to_raise = to_raise

    async def execute(self, *args: Any, **kwargs: Any) -> Any | None:
        if self._to_raise:
            raise self._to_raise
        return self._to_return

    async def get_by_id(self, *args: Any, **kwargs: Any) -> Any | None:
        if self._to_raise:
            raise self._to_raise
        return self._to_return

