from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from task_service.infrastructure.postgres.models import Comment
from task_service.schemas.comment import CommentCreate


class CommentRepository:
    """Repository for comments."""

    async def create_comment(self, session: AsyncSession, task_id: int, payload: CommentCreate) -> Comment:
        comment = Comment(task_id=task_id, user_name=payload.user_name, content=payload.content)
        session.add(comment)
        await session.flush()
        await session.refresh(comment)
        return comment

    async def list_by_task(self, session: AsyncSession, task_id: int) -> List[Comment]:
        q = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at.asc())
        result = await session.scalars(q)
        return result.all()
