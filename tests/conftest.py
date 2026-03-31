import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app
from src.models.user import Base as UserBase
from src.models.post import Base as PostBase
from src.models.like import Base as LikeBase
from src.models.reply import Base as ReplyBase
from src.core.config import JWT_SECRET_KEY
import time

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
UserBase.metadata.create_all(bind=engine)
PostBase.metadata.create_all(bind=engine)
LikeBase.metadata.create_all(bind=engine)
ReplyBase.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    def override_get_db():
        yield db_session
    app.dependency_overrides = {}
    for route in app.routes:
        if hasattr(route, "dependant"):
            for dep in route.dependant.dependencies:
                if dep.call == "src.routes.auth.get_db":
                    dep.call = override_get_db
    app.dependency_overrides["src.routes.auth.get_db"] = override_get_db
    return TestClient(app)

# Helper functions for auth

def register_user(client, username, email, password, bio="", avatar_url=""):
    return client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
        "bio": bio,
        "avatar_url": avatar_url
    })

def login_user(client, email, password):
    resp = client.post("/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None

def auth_header(token):
    return {"Authorization": f"Bearer {token}"}
