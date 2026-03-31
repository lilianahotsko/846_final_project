from pydantic import BaseModel
from typing import Optional

class LikeResponse(BaseModel):
    post_id: int
    liked: bool
    likes_count: int

    class Config:
        orm_mode = True
