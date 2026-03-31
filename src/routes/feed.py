from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from src.schemas.post import FeedResponse, PostResponse
from src.services.post_service import get_feed
from src.core.logging import logger
from src.routes.auth import get_db
from src.routes.deps import get_current_user

router = APIRouter(prefix="/feed", tags=["feed"])

@router.get("/", response_model=FeedResponse)
def get_feed_endpoint(
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    posts, next_cursor = get_feed(db, limit, cursor)
    return FeedResponse(posts=posts, next_cursor=next_cursor)
