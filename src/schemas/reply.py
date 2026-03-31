from pydantic import BaseModel, ConfigDict, constr
from datetime import datetime
from typing import List

class ReplyCreate(BaseModel):
    content: constr(strip_whitespace=True, min_length=1, max_length=280)

class ReplyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime

class RepliesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    replies: List[ReplyResponse]
