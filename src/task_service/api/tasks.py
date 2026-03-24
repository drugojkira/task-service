from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from task_service.api.depends import get_current_user
from task_service.core.exceptions.tasks import TaskNotFoundException
from task_service.core.logger import get_logger, log
from task_service.domain.use_cases.create_task import CreateTaskUseCase
from task_service.domain.use_cases.delete_task import DeleteTaskUseCase
from task_service.domain.use_cases.get_tasks import GetTasksUseCase
from task_service.domain.use_cases.get_task_statistics import GetTaskStatisticsUseCase
from task_service.domain.use_cases.update_task import UpdateTaskUseCase
from task_service.schemas.api.pagination import Pagination
from task_service.schemas.api.tasks import (
    CreateTaskRequestPayload,
    TaskResponse,
    TasksRequest,
    UpdateTaskRequestPayload,
)
from task_service.schemas.auth import AccessTokenData
from task_service.schemas.task import CreateTask, TaskFilters, UpdateTask

logger = get_logger(__name__)

tasks_router = APIRouter(prefix="/tasks")


@tasks_router.get(
    "",
    response_model=Pagination[TaskResponse],
)
@inject
@log(logger)
async def get_all_tasks(
    use_case: FromDishka[GetTasksUseCase],
    request: TasksRequest = Depends(),
) -> Pagination[TaskResponse]:
    """Получить список задач с фильтрацией и пагинацией."""
    try:
        records, total = await use_case.execute(
            filters=TaskFilters.model_validate(request.model_dump()),
        )
        return Pagination(limit=request.limit, offset=request.offset, items=records, total=total)
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@tasks_router.get(
    "/statistics",
    response_model=dict,
)
@inject
@log(logger)
async def get_task_statistics(
    use_case: FromDishka[GetTaskStatisticsUseCase],
) -> dict:
    """Получить статистику по задачам."""
    try:
        statistics = await use_case.execute()
        return statistics.model_dump()
    except Exception as e:
        logger.error(f"Error getting task statistics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@tasks_router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
@inject
@log(logger)
async def get_task(
    task_id: int,
    use_case: FromDishka[GetTasksUseCase],
) -> TaskResponse:
    """Получить задачу по ID."""
    try:
        return TaskResponse.model_validate(await use_case.get_by_id(task_id))
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@tasks_router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
@log(logger)
async def create_task(
    use_case: FromDishka[CreateTaskUseCase],
    payload: CreateTaskRequestPayload,
    current_user: AccessTokenData = Depends(get_current_user),
) -> TaskResponse:
    """Создать новую задачу."""
    try:
        return TaskResponse.model_validate(
            await use_case.execute(
                task=CreateTask(created_by=current_user.username, **payload.model_dump()),
            )
        )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@tasks_router.put(
    "/{task_id}",
    response_model=TaskResponse,
)
@inject
@log(logger)
async def update_task(
    payload: UpdateTaskRequestPayload,
    task_id: int,
    use_case: FromDishka[UpdateTaskUseCase],
    current_user: AccessTokenData = Depends(get_current_user),
) -> TaskResponse:
    """Обновить задачу."""
    try:
        return TaskResponse.model_validate(
            await use_case.execute(
                task=UpdateTask.model_validate(payload.model_dump(exclude_unset=True)),
                task_id=task_id,
                updated_by=current_user.username,
            )
        )
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@tasks_router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
@log(logger)
async def delete_task(
    task_id: int,
    use_case: FromDishka[DeleteTaskUseCase],
) -> None:
    """Удалить задачу по ID."""
    try:
        await use_case.execute(task_id=task_id)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
