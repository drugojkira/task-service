"""add comments table

Revision ID: 002
Revises: 001
Create Date: 2026-03-04 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from task_service.core.config import settings

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create comments table."""
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey(f"{settings.POSTGRES_SCHEMA}.tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_name", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        schema=settings.POSTGRES_SCHEMA,
    )

    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_comments_task_id",
        "comments",
        ["task_id"],
        schema=settings.POSTGRES_SCHEMA,
    )


def downgrade() -> None:
    """Downgrade schema: drop comments table."""
    op.drop_index(f"ix_{settings.POSTGRES_SCHEMA}_comments_task_id", table_name="comments", schema=settings.POSTGRES_SCHEMA)
    op.drop_table("comments", schema=settings.POSTGRES_SCHEMA)
