from datetime import datetime
from enum import Enum
from typing import List, Optional

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
    PRIORITY_ESCALATED = "priority_escalated"


class BaseTask(BaseModel):
    """Базовая схема задачи."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    assignees: List[str] = []
    due_date: Optional[datetime] = None


class CreateTask(BaseTask):
    """Схема для создания задачи."""

    created_by: str


class UpdateTask(BaseTask):
    """Схема для обновления задачи."""

    title: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignees: Optional[List[str]] = None


class TaskSchema(BaseTask):
    """Схема задачи из БД."""

    id: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    search_headline: Optional[str] = None


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
    assignees: List[str] = []
    status: TaskStatus
    priority: TaskPriority
    created_by: str


class TaskStatistics(BaseModel):
    """Статистика по задачам."""

    total_tasks: int
    by_status: dict[str, int]  # {"pending": 5, "in_progress": 3, ...}
    by_priority: dict[str, int]
    by_assignee: dict[str, int]
