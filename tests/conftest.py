import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, AsyncIterator, Iterator, TypeVar

import pytest
from dishka import DEFAULT_COMPONENT, AsyncContainer, Container, Provider, Scope, make_async_container
from dishka.provider import BaseProvider
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.core.config import Settings, settings as app_settings
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.repository import TaskRepository
from task_service.schemas.auth import AccessTokenData
from task_service.schemas.task import CreateTask, TaskFilters, TaskSchema, TaskStatus, TaskPriority
from tests.helpers import TestDatabase, TestDatabaseSessionWrapper


# === Event Loop ===
@pytest.fixture(scope="session")
def event_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.get_event_loop_policy().new_event_loop()


# === Settings ===
@pytest.fixture(scope="module")
def settings() -> Settings:
    return app_settings


# === Database ===
@pytest.fixture
def test_database(settings: Settings) -> TestDatabase:
    return TestDatabase(settings.postgres_url)


@pytest.fixture
async def async_session(test_database: TestDatabase) -> AsyncIterator[AsyncSession]:
    async with test_database.session() as session:
        yield session


@pytest.fixture
def db_with_active_session(async_session: AsyncSession) -> TestDatabaseSessionWrapper:
    return TestDatabaseSessionWrapper(async_session)


# === Repositories ===
@pytest.fixture
def task_repository() -> TaskRepository:
    return TaskRepository()


# === App & Client ===
@pytest.fixture
def app() -> Iterator[FastAPI]:
    from task_service.app import app
    yield app


@pytest.fixture
async def test_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# === Test Data ===
@pytest.fixture
def test_current_user() -> AccessTokenData:
    return AccessTokenData(username="test_user")


@pytest.fixture
def valid_create_task() -> CreateTask:
    return CreateTask(
        title="Test Task",
        description="Test Description",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        assignee="test_assignee",
        created_by="test_user",
    )


@pytest.fixture
def valid_task_schema(valid_create_task: CreateTask) -> TaskSchema:
    now = datetime.now(timezone.utc)
    return TaskSchema(
        id=1,
        title=valid_create_task.title,
        description=valid_create_task.description,
        status=valid_create_task.status,
        priority=valid_create_task.priority,
        assignee=valid_create_task.assignee,
        due_date=None,
        created_by=valid_create_task.created_by,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def valid_task_filters() -> TaskFilters:
    return TaskFilters(limit=10, offset=0)


# === DI Override helpers ===
def _container_provider(container: AsyncContainer) -> BaseProvider:
    container_provider = BaseProvider(component=DEFAULT_COMPONENT)
    container_provider.factories.extend(container.registry.factories.values())
    for registry in container.child_registries:
        container_provider.factories.extend(registry.factories.values())
    return container_provider


CT = TypeVar("CT", Container, AsyncContainer)


def _swap(c1: CT, c2: CT) -> None:
    for attr in type(c1).__slots__:
        tmp = getattr(c1, attr)
        setattr(c1, attr, getattr(c2, attr))
        setattr(c2, attr, tmp)


@asynccontextmanager
async def override(container: AsyncContainer, *providers: BaseProvider) -> AsyncGenerator:
    new_container = make_async_container(_container_provider(container), *providers)
    _swap(container, new_container)
    yield
    await container.close()
    _swap(new_container, container)



