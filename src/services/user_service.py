from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.models.user import User
from src.core.security import hash_password, verify_password, create_access_token
from src.schemas.user import UserCreate, UserLogin
from fastapi import HTTPException, status
from src.core.logging import logger
import re

def normalize_username(username: str) -> str:
    return username.lower()

def create_user(db: Session, user_in: UserCreate):
    username_norm = normalize_username(user_in.username)
    user = User(
        username=username_norm,
        email=user_in.email.lower(),
        password_hash=hash_password(user_in.password),
        bio=user_in.bio,
        avatar_url=user_in.avatar_url,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        logger.info(
            "User registered",
            extra={"action": "register", "user_id": user.id, "resource_id": user.id},
        )
        return user
    except IntegrityError as e:
        db.rollback()
        orig_msg = str(e.orig).lower()
        if "ix_users_username_ci" in orig_msg or "users.username" in orig_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "USERNAME_TAKEN", "message": "Username already exists."}},
            )
        if "users_email_key" in orig_msg or "users.email" in orig_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "EMAIL_TAKEN", "message": "Email already exists."}},
            )
        raise

def authenticate_user(db: Session, user_in: UserLogin):
    user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        logger.warning(
            "Failed login",
            extra={"action": "login", "user_id": None, "resource_id": None},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."}},
        )
    logger.info(
        "User login",
        extra={"action": "login", "user_id": user.id, "resource_id": user.id},
    )
    return user

def generate_token(user: User):
    token = create_access_token({"sub": str(user.id)})
    return token
