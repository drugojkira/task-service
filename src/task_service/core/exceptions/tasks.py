from typing import Final

from task_service.core.exceptions.base import BaseServiceException, EntityNotFoundException


class TaskNotFoundException(EntityNotFoundException):
    """Задача не найдена."""

    def __init__(self, task_id: int) -> None:
        super().__init__(entity="Task", entity_id=task_id)


class TaskValidationError(BaseServiceException):
    """Ошибка валидации задачи."""
    pass


class TaskOperationError(BaseServiceException):
    """Ошибка операции над задачей."""
    pass


class TaskAlreadyExistsError(BaseServiceException):
    """Задача уже существует."""

    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Задача с названием '{title}' уже существует"

    def __init__(self, title: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(title=title)
        super().__init__(self.message)



