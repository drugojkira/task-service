import asyncio
import logging

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from tenacity import before_sleep_log, retry, wait_exponential

from task_service.core.config import settings
from task_service.infrastructure.postgres.base import Base
from task_service.infrastructure.postgres.models import Task, TaskHistory  # noqa: F401

CREATE_SCHEMA_QUERY = f"CREATE SCHEMA IF NOT EXISTS {settings.POSTGRES_SCHEMA};"

config = context.config
logger = logging.getLogger(__name__)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", settings.postgres_url)


def filter_foreign_schemas(name, type_, parent_names):
    return type_ != "schema" or name == settings.POSTGRES_SCHEMA


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema=settings.POSTGRES_SCHEMA,
        include_schemas=True,
        include_name=filter_foreign_schemas,
    )

    with context.begin_transaction():
        context.execute(CREATE_SCHEMA_QUERY)
        context.run_migrations()


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.ERROR),
)
async def run_migrations_online(engine: AsyncEngine):
    """Run migrations in 'online' mode."""
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        ),
    )

    asyncio.run(run_migrations_online(connectable))
