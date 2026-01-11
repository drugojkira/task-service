from typing import Final

from task_service.core.exceptions.base import BaseServiceException


class RabbitMQConnectionError(BaseServiceException):
    """Ошибка подключения к RabbitMQ."""

    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Не удалось подключиться к RabbitMQ: {detail}"

    def __init__(self, detail: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(detail=detail)
        super().__init__(self.message)


class RabbitMQPublishError(BaseServiceException):
    """Ошибка публикации сообщения."""

    _ERROR_MESSAGE_TEMPLATE: Final[str] = "Не удалось опубликовать сообщение: {detail}"

    def __init__(self, detail: str) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(detail=detail)
        super().__init__(self.message)



