from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class CommentCreate(BaseModel):
    user_name: Optional[str] = None
    content: str


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_name: str
    content: str
    created_at: datetime
    updated_at: datetime
