from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from task_service.api.health_check.health_check_router import health_check_router
from task_service.api.metrics import metrics_router
from task_service.api.tasks import tasks_router
from task_service.api.comments import comments_router
from task_service.core.config import settings
from task_service.core.providers.setup import container
from task_service.domain.metrics.registry_metrics import setup_metrics
from task_service.infrastructure.rabbitmq.broker import broker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan для подключения/отключения RabbitMQ broker."""
    await broker.connect()
    yield
    await broker.close()


def create_app() -> FastAPI:
    """Создание приложения FastAPI."""
    app = FastAPI(
        title="Task Service",
        description="Сервис управления задачами",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        root_path=settings.ROOT_PATH,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Роутеры
    app.include_router(tasks_router, prefix="/api/v1", tags=["Tasks"])
    app.include_router(comments_router, prefix="/api/v1", tags=["Comments"])
    app.include_router(health_check_router)
    app.include_router(metrics_router)

    # DI контейнер
    setup_dishka(container, app)

    # Метрики
    setup_metrics(app)

    return app


app = create_app()
