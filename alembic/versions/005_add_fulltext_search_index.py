"""add GIN index for full-text search on tasks

Revision ID: 005
Revises: 004
Create Date: 2026-04-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

from task_service.core.config import settings

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create GIN index for full-text search on title + description."""
    op.execute(
        f"""
        CREATE INDEX idx_tasks_fulltext
        ON {settings.POSTGRES_SCHEMA}.tasks
        USING GIN(
            to_tsvector('russian', coalesce(title, '') || ' ' || coalesce(description, ''))
        );
        """
    )


def downgrade() -> None:
    """Drop full-text search index."""
    op.execute(
        f"DROP INDEX IF EXISTS {settings.POSTGRES_SCHEMA}.idx_tasks_fulltext;"
    )
