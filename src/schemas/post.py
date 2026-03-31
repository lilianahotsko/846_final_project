from pydantic import BaseModel, constr
from typing import List, Optional

class PostCreate(BaseModel):
    content: constr(strip_whitespace=True, min_length=1, max_length=280)

class PostResponse(BaseModel):
    id: int
    user_id: int
    content: str
    created_at: str

    class Config:
        orm_mode = True

class FeedResponse(BaseModel):
    posts: List[PostResponse]
    next_cursor: Optional[str] = None
