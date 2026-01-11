from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

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
