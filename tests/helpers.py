from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from task_service.infrastructure.postgres.database import Database


class TestDatabase(Database):
    """База данных для тестов с rollback после каждого теста."""

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            try:
                yield session
            finally:
                await session.rollback()


class TestDatabaseSessionWrapper(Database):
    """Обёртка для использования существующей сессии в тестах."""

    __test__ = False

    def __init__(self, session: AsyncSession):
        self._session = session

    @property
    def active_session(self) -> AsyncSession:
        return self._session

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        yield self._session



