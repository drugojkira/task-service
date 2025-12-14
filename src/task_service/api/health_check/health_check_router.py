from fastapi import APIRouter
from pydantic import BaseModel

health_check_router = APIRouter(tags=["Health check"])


class HealthResponse(BaseModel):
    status: str
    service: str


@health_check_router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Проверка здоровья сервиса."""
    return HealthResponse(status="healthy", service="task-service")


@health_check_router.get("/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Проверка готовности сервиса."""
    return HealthResponse(status="ready", service="task-service")

