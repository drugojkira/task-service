from pydantic import BaseModel


class AccessTokenData(BaseModel):
    """Данные из токена доступа."""

    username: str
    user_id: int | None = None

