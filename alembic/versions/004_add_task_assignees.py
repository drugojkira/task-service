"""add task_assignees table

Revision ID: 004
Revises: 003
Create Date: 2026-04-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from task_service.core.config import settings

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create task_assignees table."""
    op.create_table(
        "task_assignees",
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey(f"{settings.POSTGRES_SCHEMA}.tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assignee_email", sa.String(length=255), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(),
            server_default=sa.text("timezone('UTC', CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("task_id", "assignee_email"),
        schema=settings.POSTGRES_SCHEMA,
    )

    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_task_assignees_task_id",
        "task_assignees",
        ["task_id"],
        schema=settings.POSTGRES_SCHEMA,
    )

    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_task_assignees_assignee_email",
        "task_assignees",
        ["assignee_email"],
        schema=settings.POSTGRES_SCHEMA,
    )

    # Migrate existing assignee data into the new table
    op.execute(
        f"""
        INSERT INTO {settings.POSTGRES_SCHEMA}.task_assignees (task_id, assignee_email)
        SELECT id, assignee FROM {settings.POSTGRES_SCHEMA}.tasks
        WHERE assignee IS NOT NULL AND assignee != ''
        """
    )


def downgrade() -> None:
    """Downgrade schema: drop task_assignees table."""
    op.drop_index(
        f"ix_{settings.POSTGRES_SCHEMA}_task_assignees_assignee_email",
        table_name="task_assignees",
        schema=settings.POSTGRES_SCHEMA,
    )
    op.drop_index(
        f"ix_{settings.POSTGRES_SCHEMA}_task_assignees_task_id",
        table_name="task_assignees",
        schema=settings.POSTGRES_SCHEMA,
    )
    op.drop_table("task_assignees", schema=settings.POSTGRES_SCHEMA)
