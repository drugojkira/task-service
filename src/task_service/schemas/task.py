from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskStatus(str, Enum):
    """Статусы задачи."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Приоритеты задачи."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskEventType(str, Enum):
    """Типы событий задачи."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"


class BaseTask(BaseModel):
    """Базовая схема задачи."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None


class CreateTask(BaseTask):
    """Схема для создания задачи."""

    created_by: str


class UpdateTask(BaseTask):
    """Схема для обновления задачи."""

    title: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None


class TaskSchema(BaseTask):
    """Схема задачи из БД."""

    id: int
    created_by: str
    created_at: datetime
    updated_at: datetime


# ======== Межслойные DTO (Filters) ========

class TaskFilters(BaseModel):
    """Фильтры для получения задач - межслойная DTO."""

    limit: int
    offset: int
    search: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    created_by: Optional[str] = None
    created_at_gte: Optional[datetime] = None
    created_at_lte: Optional[datetime] = None


# ======== RabbitMQ Messages ========

class TaskNotificationMessage(BaseModel):
    """Сообщение для RabbitMQ о событии задачи."""

    task_id: int
    event_type: TaskEventType
    task_title: str
    task_description: Optional[str] = None
    assignee: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    created_by: str
