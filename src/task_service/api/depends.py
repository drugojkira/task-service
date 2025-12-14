"""Зависимости для API."""

from fastapi import Header

from task_service.schemas.auth import AccessTokenData


async def get_current_user(
    x_user_name: str = Header(default="anonymous"),
    x_user_id: int | None = Header(default=None),
) -> AccessTokenData:
    """
    Получить текущего пользователя из заголовков.
    
    В реальном проекте здесь была бы валидация JWT токена.
    """
    return AccessTokenData(username=x_user_name, user_id=x_user_id)
