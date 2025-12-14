from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from prometheus_client import generate_latest
from starlette.responses import Response

from task_service.domain.metrics.registry_metrics import instrumentator, task_service_registry
from task_service.domain.metrics.use_case import GetTasksMetricsUseCase

metrics_router = APIRouter()


@metrics_router.get("/metrics", include_in_schema=False)
@inject
async def metrics(use_case: FromDishka[GetTasksMetricsUseCase]) -> Response:
    await use_case.execute()
    return Response(
        content=generate_latest(task_service_registry) + generate_latest(instrumentator.registry),
        media_type="text/plain",
    )
