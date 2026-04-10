from datetime import datetime
from typing import List, Optional

from fastapi import Query
from pydantic import BaseModel, Field

from task_service.schemas.api.pagination import PaginationAwareRequest
from task_service.schemas.task import TaskPriority, TaskStatus


class TasksRequest(PaginationAwareRequest):
    """Запрос списка задач с фильтрацией."""

    search: Optional[str] = Field(
        None,
        description="Часть названия для поиска (регистронезависимо)",
        example="bug",
    )
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    created_by: Optional[str] = None
    created_at_gte: Optional[datetime] = None
    created_at_lte: Optional[datetime] = None


class TaskIDs(BaseModel):
    """Список ID задач."""

    ids: list[int] = Field(Query(default_factory=list))


class CreateTaskRequestPayload(BaseModel):
    """Payload для создания задачи."""

    title: str = Field(..., min_length=1, max_length=255, description="Название задачи")
    description: Optional[str] = Field(None, max_length=2000, description="Описание задачи")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Статус задачи")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Приоритет задачи")
    assignee: Optional[str] = Field(None, max_length=100, description="Исполнитель (обратная совместимость)")
    assignees: List[str] = Field(default_factory=list, description="Список исполнителей")
    due_date: Optional[datetime] = Field(None, description="Срок выполнения")


class UpdateTaskRequestPayload(BaseModel):
    """Payload для обновления задачи."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = Field(None, max_length=100, description="Исполнитель (обратная совместимость)")
    assignees: Optional[List[str]] = Field(None, description="Список исполнителей")
    due_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    """Ответ с данными задачи."""

    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    assignees: List[str] = []
    due_date: Optional[datetime]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



