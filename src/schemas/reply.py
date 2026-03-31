from pydantic import BaseModel, constr
from typing import List

class ReplyCreate(BaseModel):
    content: constr(strip_whitespace=True, min_length=1, max_length=280)

class ReplyResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    created_at: str

    class Config:
        orm_mode = True

class RepliesResponse(BaseModel):
    replies: List[ReplyResponse]
