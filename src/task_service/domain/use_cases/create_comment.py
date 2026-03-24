from task_service.core.logger import get_logger, log
from task_service.infrastructure.postgres.database import Database
from task_service.infrastructure.postgres.comment_repository import CommentRepository
from task_service.schemas.comment import CommentCreate, CommentResponse

logger = get_logger(__name__)


class CreateCommentUseCase:
    def __init__(self, database: Database, repository: CommentRepository):
        self._database = database
        self._repository = repository

    @log(logger)
    async def execute(self, task_id: int, payload: CommentCreate) -> CommentResponse:
        async with self._database.session() as session:
            comment = await self._repository.create_comment(session, task_id, payload)
        return CommentResponse.model_validate(comment)
