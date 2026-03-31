from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.models.reply import Reply
from src.models.post import Post
from src.schemas.reply import ReplyCreate
from fastapi import HTTPException, status
from src.core.logging import logger
from datetime import datetime, timedelta

REPLY_LIMIT_PER_HOUR = 50


def create_reply(db: Session, user_id: int, post_id: int, reply_in: ReplyCreate):
    # Check post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        logger.warning(
            "Post not found for reply",
            extra={"action": "create_reply", "user_id": user_id, "resource_id": post_id},
        )
        raise HTTPException(status_code=404, detail={"error": {"code": "POST_NOT_FOUND", "message": "Post not found."}})

    # Enforce reply-to-post only (not reply-to-reply)
    # (No reply_id in input, so only possible to reply to posts)

    # Rate limit: max 50 replies/hour per user
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_replies = db.query(Reply).filter(
        Reply.user_id == user_id,
        Reply.created_at >= one_hour_ago
    ).count()
    if recent_replies >= REPLY_LIMIT_PER_HOUR:
        logger.warning(
            "Reply rate limit exceeded",
            extra={"action": "create_reply", "user_id": user_id, "resource_id": post_id},
        )
        raise HTTPException(status_code=429, detail={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Reply rate limit exceeded."}})

    reply = Reply(post_id=post_id, user_id=user_id, content=reply_in.content)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    logger.info(
        "Reply created",
        extra={"action": "create_reply", "user_id": user_id, "resource_id": reply.id},
    )
    return reply

def get_replies(db: Session, post_id: int):
    replies = db.query(Reply).filter(Reply.post_id == post_id).order_by(Reply.created_at.asc()).all()
    return replies
