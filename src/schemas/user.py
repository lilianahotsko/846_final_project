from pydantic import BaseModel, ConfigDict, EmailStr, constr, field_validator
from datetime import datetime
import re

USERNAME_REGEX = r"^[A-Za-z0-9_]{3,32}$"

class UserCreate(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=32, pattern=USERNAME_REGEX)
    email: EmailStr
    password: constr(min_length=8, max_length=128)
    bio: constr(max_length=160) = ""
    avatar_url: constr(max_length=2048) = ""

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v):
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("Password must contain at least one letter and one number.")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=128)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    bio: str = ""
    avatar_url: str = ""
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
