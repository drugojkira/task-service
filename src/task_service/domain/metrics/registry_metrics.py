from fastapi import FastAPI
from prometheus_client import CollectorRegistry, Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

task_service_registry = CollectorRegistry()

instrumentator = Instrumentator()

# === Бизнес-метрики ===
TASKS_CREATED = Counter(
    "task_service_tasks_created_total",
    "Total number of tasks created",
    registry=task_service_registry,
)
TASKS_UPDATED = Counter(
    "task_service_tasks_updated_total",
    "Total number of tasks updated",
    registry=task_service_registry,
)
TASKS_DELETED = Counter(
    "task_service_tasks_deleted_total",
    "Total number of tasks deleted",
    registry=task_service_registry,
)

# === Gauge метрики ===
TASKS_TOTAL = Gauge(
    "task_service_tasks_total",
    "Current total number of tasks",
    registry=task_service_registry,
)
TASKS_BY_STATUS = Gauge(
    "task_service_tasks_by_status",
    "Current number of tasks by status",
    ["status"],
    registry=task_service_registry,
)
TASKS_BY_PRIORITY = Gauge(
    "task_service_tasks_by_priority",
    "Current number of tasks by priority",
    ["priority"],
    registry=task_service_registry,
)


def setup_metrics(app: FastAPI) -> None:
    instrumentator.instrument(app)



