from datetime import datetime

from typing import List

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from task_service.infrastructure.postgres.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default="todo",
        server_default="todo",
    )
    priority: Mapped[str] = mapped_column(
        String(50),
        default="medium",
        server_default="medium",
    )
    assignee: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)

    task_assignees: Mapped[List["TaskAssignee"]] = relationship(
        "TaskAssignee", back_populates="task", cascade="all, delete-orphan", lazy="selectin",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.timezone("UTC", func.current_timestamp()),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.timezone("UTC", func.current_timestamp()),
        onupdate=func.timezone("UTC", func.current_timestamp()),
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(index=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.timezone("UTC", func.current_timestamp())
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.timezone("UTC", func.current_timestamp()), onupdate=func.timezone("UTC", func.current_timestamp())
    )


class TaskAssignee(Base):
    __tablename__ = "task_assignees"

    task_id: Mapped[int] = mapped_column(
        ForeignKey("task_service.tasks.id", ondelete="CASCADE"), primary_key=True,
    )
    assignee_email: Mapped[str] = mapped_column(String(255), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.timezone("UTC", func.current_timestamp()),
    )

    task: Mapped["Task"] = relationship("Task", back_populates="task_assignees")


class TaskHistory(Base):
    __tablename__ = "task_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(index=True)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    changes: Mapped[dict] = mapped_column(JSON, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.timezone("UTC", func.current_timestamp()),
    )
