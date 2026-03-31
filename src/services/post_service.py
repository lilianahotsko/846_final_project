from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from src.models.post import Post
from src.models.user import User
from fastapi import HTTPException, status
from src.core.logging import logger
from typing import Optional, List

def create_post(db: Session, user: User, content: str) -> Post:
    if not content or len(content) > 280:
        logger.warning(
            "Invalid post content",
            extra={"action": "create_post", "user_id": user.id, "resource_id": None},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_CONTENT", "message": "Content must be 1-280 characters."}},
        )
    post = Post(user_id=user.id, content=content)
    db.add(post)
    db.commit()
    db.refresh(post)
    logger.info(
        "Post created",
        extra={"action": "create_post", "user_id": user.id, "resource_id": post.id},
    )
    return post

def delete_post(db: Session, user: User, post_id: int):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        logger.warning(
            "Post not found for deletion",
            extra={"action": "delete_post", "user_id": user.id, "resource_id": post_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "POST_NOT_FOUND", "message": "Post not found."}},
        )
    if post.user_id != user.id:
        logger.warning(
            "Forbidden post deletion",
            extra={"action": "delete_post", "user_id": user.id, "resource_id": post.id},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Not authorized to delete this post."}},
        )
    db.delete(post)
    db.commit()
    logger.info(
        "Post deleted",
        extra={"action": "delete_post", "user_id": user.id, "resource_id": post.id},
    )

def get_feed(db: Session, limit: int = 20, cursor: Optional[str] = None) -> (List[Post], Optional[str]):
    limit = min(max(limit, 1), 100)
    query = db.query(Post).order_by(Post.created_at.desc(), Post.id.desc())
    if cursor:
        # Cursor is expected as "created_at|id"
        try:
            created_at_str, id_str = cursor.split("|")
            from datetime import datetime
            created_at = datetime.fromisoformat(created_at_str)
            id_val = int(id_str)
            query = query.filter(
                (Post.created_at < created_at) |
                (and_(Post.created_at == created_at, Post.id < id_val))
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "INVALID_CURSOR", "message": "Invalid cursor format."}},
            )
    posts = query.limit(limit + 1).all()
    next_cursor = None
    if len(posts) > limit:
        last = posts[limit - 1]
        next_cursor = f"{last.created_at.isoformat()}|{last.id}"
        posts = posts[:limit]
    logger.info(
        "Feed accessed",
        extra={"action": "get_feed", "user_id": None, "resource_id": None},
    )
    return posts, next_cursor
