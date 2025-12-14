"""init tasks table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from task_service.core.config import settings

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), server_default="todo", nullable=False),
        sa.Column("priority", sa.String(50), server_default="medium", nullable=False),
        sa.Column("assignee", sa.String(100), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("timezone('UTC', CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("timezone('UTC', CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema=settings.POSTGRES_SCHEMA,
    )

    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_tasks_title",
        "tasks",
        ["title"],
        schema=settings.POSTGRES_SCHEMA,
    )
    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_tasks_assignee",
        "tasks",
        ["assignee"],
        schema=settings.POSTGRES_SCHEMA,
    )
    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_tasks_status",
        "tasks",
        ["status"],
        schema=settings.POSTGRES_SCHEMA,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(f"ix_{settings.POSTGRES_SCHEMA}_tasks_status", table_name="tasks", schema=settings.POSTGRES_SCHEMA)
    op.drop_index(f"ix_{settings.POSTGRES_SCHEMA}_tasks_assignee", table_name="tasks", schema=settings.POSTGRES_SCHEMA)
    op.drop_index(f"ix_{settings.POSTGRES_SCHEMA}_tasks_title", table_name="tasks", schema=settings.POSTGRES_SCHEMA)
    op.drop_table("tasks", schema=settings.POSTGRES_SCHEMA)
