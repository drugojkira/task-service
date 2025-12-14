from sqlalchemy.orm import DeclarativeBase

from task_service.core.config import settings


class Base(DeclarativeBase):
    __table_args__ = {"schema": settings.POSTGRES_SCHEMA}

