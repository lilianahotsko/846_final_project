import sys
import os
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from src.models.user import User
from src.core.security import hash_password
from src.core.config import DATABASE_URL

engine = sqlalchemy.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def main():
    username = "lhotsko"
    email = "nanigock@gmail.com"
    password = "12345678"
    bio = ""
    avatar_url = ""
    password_hash = hash_password(password)
    session = SessionLocal()
    try:
        # Check if user already exists
        existing = session.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing:
            print("User already exists.")
            return
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            bio=bio,
            avatar_url=avatar_url,
        )
        session.add(user)
        session.commit()
        print("User created successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
