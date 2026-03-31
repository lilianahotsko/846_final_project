from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.schemas.reply import ReplyCreate, ReplyResponse, RepliesResponse
from src.services.reply_service import create_reply, get_replies
from src.routes.auth import get_db
from src.routes.deps import get_current_user
from src.core.logging import logger

router = APIRouter(prefix="/posts/{post_id}/replies", tags=["replies"])

@router.post("/", response_model=ReplyResponse, status_code=status.HTTP_201_CREATED)
def create_reply_endpoint(
    post_id: int,
    reply_in: ReplyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    reply = create_reply(db, current_user.id, post_id, reply_in)
    return reply

@router.get("/", response_model=RepliesResponse)
def get_replies_endpoint(
    post_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    replies = get_replies(db, post_id)
    return RepliesResponse(replies=replies)
