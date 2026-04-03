"""add task_history table

Revision ID: 003
Revises: 002
Create Date: 2026-04-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from task_service.core.config import settings

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create task_history table."""
    op.create_table(
        "task_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "task_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("changed_by", sa.String(length=255), nullable=False),
        sa.Column("change_type", sa.String(length=50), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(),
            server_default=sa.text("timezone('UTC', CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=settings.POSTGRES_SCHEMA,
    )

    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_task_history_task_id",
        "task_history",
        ["task_id"],
        schema=settings.POSTGRES_SCHEMA,
    )

    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_task_history_change_type",
        "task_history",
        ["change_type"],
        schema=settings.POSTGRES_SCHEMA,
    )


def downgrade() -> None:
    """Downgrade schema: drop task_history table."""
    op.drop_index(
        f"ix_{settings.POSTGRES_SCHEMA}_task_history_change_type",
        table_name="task_history",
        schema=settings.POSTGRES_SCHEMA,
    )
    op.drop_index(
        f"ix_{settings.POSTGRES_SCHEMA}_task_history_task_id",
        table_name="task_history",
        schema=settings.POSTGRES_SCHEMA,
    )
    op.drop_table("task_history", schema=settings.POSTGRES_SCHEMA)
