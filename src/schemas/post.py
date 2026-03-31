from pydantic import BaseModel, ConfigDict, constr
from datetime import datetime
from typing import List, Optional

class PostCreate(BaseModel):
    content: constr(strip_whitespace=True, min_length=1, max_length=280)

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    content: str
    created_at: datetime

class FeedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    posts: List[PostResponse]
    next_cursor: Optional[str] = None
