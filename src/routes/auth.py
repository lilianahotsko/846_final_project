from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from src.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from src.services.user_service import create_user, authenticate_user, generate_token
from src.core.logging import logger


router = APIRouter(prefix="/auth", tags=["auth"])


from src.routes.deps import get_db

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = create_user(db, user_in)
    return user

@router.post("/login", response_model=TokenResponse)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_in)
    token = generate_token(user)
    return {"access_token": token, "token_type": "bearer"}
