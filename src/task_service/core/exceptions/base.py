from typing import Final


class BaseServiceException(Exception):
    """Базовое исключение сервиса."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(BaseServiceException):
    """Сущность не найдена."""

    _ERROR_MESSAGE_TEMPLATE: Final[str] = "{entity} с id={entity_id} не найден"

    def __init__(self, entity: str, entity_id: int) -> None:
        self.message = self._ERROR_MESSAGE_TEMPLATE.format(entity=entity, entity_id=entity_id)
        super().__init__(self.message)



