from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Index
from src.models.base import Base

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(String(280), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_posts_created_at_desc", created_at.desc()),
        Index("ix_posts_user_id", user_id),
    )
