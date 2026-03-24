from typing import List

from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.comment_repository import CommentRepository
from task_service.schemas.comment import CommentResponse

logger = get_logger(__name__)


class GetTaskCommentsUseCase:
    def __init__(self, database: Database, repository: CommentRepository):
        self._database = database
        self._repository = repository

    @log(logger)
    async def execute(self, task_id: int) -> List[CommentResponse]:
        async with self._database.session() as session:
            comments = await self._repository.list_by_task(session, task_id)
        return [CommentResponse.model_validate(c) for c in comments]
