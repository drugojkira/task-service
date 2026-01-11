from typing import Generic, List, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field


class PaginationAwareRequest(BaseModel):
    """Базовый класс для запросов с пагинацией."""

    limit: int = Query(100)
    offset: int = Query(0)


T = TypeVar("T")


class Pagination(BaseModel, Generic[T]):
    """
    Pagination model.
    
    Wrap a generic list of items with skip, limit and counter.
    """

    limit: int = 10
    offset: int = 0
    count: int = 0
    total: int = 0
    items: List[T] = Field(default_factory=list)

    def __init__(self, **data) -> None:  # type: ignore
        data.setdefault("count", len(data.get("items", [])))
        super().__init__(**data)



