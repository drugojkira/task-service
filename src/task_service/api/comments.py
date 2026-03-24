from typing import List

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from task_service.api.depends import get_current_user
from task_service.core.logger import get_logger, log
from task_service.domain.use_cases.create_comment import CreateCommentUseCase
from task_service.domain.use_cases.get_task_comments import GetTaskCommentsUseCase
from task_service.schemas.comment import CommentCreate, CommentResponse
from task_service.schemas.auth import AccessTokenData

logger = get_logger(__name__)

comments_router = APIRouter(prefix="/tasks/{task_id}/comments")


@comments_router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
@inject
@log(logger)
async def create_comment(
    task_id: int,
    payload: CommentCreate,
    use_case: FromDishka[CreateCommentUseCase],
    current_user: AccessTokenData = Depends(get_current_user),
) -> CommentResponse:
    try:
        # we use provided user_name from headers if not provided in payload
        payload.user_name = current_user.username
        return CommentResponse.model_validate(await use_case.execute(task_id=task_id, payload=payload))
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@comments_router.get("", response_model=List[CommentResponse])
@inject
@log(logger)
async def list_comments(task_id: int, use_case: FromDishka[GetTaskCommentsUseCase]) -> List[CommentResponse]:
    try:
        return await use_case.execute(task_id=task_id)
    except Exception as e:
        logger.error(f"Error listing comments: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
