from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.models.like import Like
from src.models.post import Post
from src.models.user import User
from src.core.logging import logger
from fastapi import HTTPException, status
from sqlalchemy import func

def like_post(db: Session, user_id: int, post_id: int):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        logger.warning(
            "Post not found for like",
            extra={"action": "like_post", "user_id": user_id, "resource_id": post_id},
        )
        raise HTTPException(status_code=404, detail={"error": {"code": "POST_NOT_FOUND", "message": "Post not found."}})
    like = db.query(Like).filter(Like.user_id == user_id, Like.post_id == post_id).first()
    if like:
        # Already liked, idempotent
        likes_count = db.query(func.count(Like.id)).filter(Like.post_id == post_id).scalar()
        logger.info(
            "Like idempotent",
            extra={"action": "like_post", "user_id": user_id, "resource_id": post_id},
        )
        return True, likes_count
    try:
        new_like = Like(user_id=user_id, post_id=post_id)
        db.add(new_like)
        db.commit()
        likes_count = db.query(func.count(Like.id)).filter(Like.post_id == post_id).scalar()
        logger.info(
            "Post liked",
            extra={"action": "like_post", "user_id": user_id, "resource_id": post_id},
        )
        return True, likes_count
    except IntegrityError:
        db.rollback()
        likes_count = db.query(func.count(Like.id)).filter(Like.post_id == post_id).scalar()
        logger.info(
            "Like idempotent (race)",
            extra={"action": "like_post", "user_id": user_id, "resource_id": post_id},
        )
        return True, likes_count

def unlike_post(db: Session, user_id: int, post_id: int):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        logger.warning(
            "Post not found for unlike",
            extra={"action": "unlike_post", "user_id": user_id, "resource_id": post_id},
        )
        raise HTTPException(status_code=404, detail={"error": {"code": "POST_NOT_FOUND", "message": "Post not found."}})
    like = db.query(Like).filter(Like.user_id == user_id, Like.post_id == post_id).first()
    if not like:
        likes_count = db.query(func.count(Like.id)).filter(Like.post_id == post_id).scalar()
        logger.info(
            "Unlike idempotent",
            extra={"action": "unlike_post", "user_id": user_id, "resource_id": post_id},
        )
        return False, likes_count
    db.delete(like)
    db.commit()
    likes_count = db.query(func.count(Like.id)).filter(Like.post_id == post_id).scalar()
    logger.info(
        "Post unliked",
        extra={"action": "unlike_post", "user_id": user_id, "resource_id": post_id},
    )
    return True, likes_count
