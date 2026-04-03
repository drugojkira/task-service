from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskHistorySchema(BaseModel):
    """Схема записи истории задачи из БД."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    changed_by: str
    change_type: str
    changes: dict
    changed_at: datetime


class TaskHistoryFilters(BaseModel):
    """Фильтры для получения истории задачи."""

    change_type: Optional[str] = None
    changed_at_gte: Optional[datetime] = None
    changed_at_lte: Optional[datetime] = None
