from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from src.schemas.post import PostCreate, PostResponse, FeedResponse
from src.services.post_service import create_post, delete_post, get_feed
from src.core.logging import logger
from src.routes.deps import get_db
from src.routes.deps import get_current_user
from src.models.user import User

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post_endpoint(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = create_post(db, current_user, post_in.content)
    return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_endpoint(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_post(db, current_user, post_id)
    return
