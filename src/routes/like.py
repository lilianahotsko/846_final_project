from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.core.logging import logger
from src.routes.deps import get_db
from src.routes.deps import get_current_user
from src.services.like_service import like_post, unlike_post
from src.schemas.like import LikeResponse

router = APIRouter(prefix="/posts", tags=["likes"])

@router.post("/{id}/like", response_model=LikeResponse, status_code=status.HTTP_200_OK)
def like_post_endpoint(id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    liked, likes_count = like_post(db, current_user.id, id)
    return LikeResponse(post_id=id, liked=liked, likes_count=likes_count)

@router.delete("/{id}/like", response_model=LikeResponse, status_code=status.HTTP_200_OK)
def unlike_post_endpoint(id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    unliked, likes_count = unlike_post(db, current_user.id, id)
    return LikeResponse(post_id=id, liked=not unliked, likes_count=likes_count)
