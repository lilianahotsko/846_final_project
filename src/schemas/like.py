from pydantic import BaseModel, ConfigDict
from typing import Optional

class LikeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: int
    liked: bool
    likes_count: int
