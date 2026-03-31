import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool

from src.main import app
from src.models.base import Base
# Import all models so their tables are registered on Base.metadata
import src.models.user  # noqa: F401
import src.models.post  # noqa: F401
import src.models.like  # noqa: F401
import src.models.reply  # noqa: F401
from src.routes.deps import get_db

# ── SQLite in-memory engine ───────────────────────────────────────────────────
# StaticPool ensures all sessions share the same connection, so tables created
# by setup_db are visible to every request handler during the test run.
_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

# ── Unique suffix so parallel runs never collide ──────────────────────────────
SUFFIX = uuid.uuid4().hex[:8]


def _user(n: int) -> dict:
    return {
        "username": f"tst{SUFFIX}{n}",
        "email": f"tst{SUFFIX}{n}@example.com",
        "password": "TestPass123",
        "bio": f"Test user {n}",
        "avatar_url": "",
    }


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Create all tables once before this module's tests; drop them after."""
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture(scope="module")
def client(setup_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def tokens(client):
    """
    Register users 1-3 (idempotent) and return their tokens.
    Returns: {1: token1, 2: token2, 3: token3}
    """
    result = {}
    for n in (1, 2, 3):
        data = _user(n)
        client.post("/auth/register", json=data)  # ignore if already exists
        resp = client.post("/auth/login", json={"email": data["email"], "password": data["password"]})
        assert resp.status_code == 200, f"Login failed for user {n}: {resp.text}"
        result[n] = resp.json()["access_token"]
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────────────────

class TestRegistration:
    def test_register_three_users(self, client):
        for n in (1, 2, 3):
            resp = client.post("/auth/register", json=_user(n))
            # 201 Created, or 400/409 if tokens fixture registered them first
            assert resp.status_code in (201, 400, 409), resp.text

    def test_register_returns_expected_fields(self, client):
        unique = uuid.uuid4().hex[:6]
        payload = {
            "username": f"new{unique}",
            "email": f"new{unique}@example.com",
            "password": "TestPass123",
            "bio": "Fresh user",
            "avatar_url": "",
        }
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["username"] == payload["username"]
        assert body["email"] == payload["email"]
        assert "id" in body
        assert "created_at" in body

    def test_register_duplicate_username_fails(self, client, tokens):
        """Registering the same username twice must be rejected."""
        resp = client.post("/auth/register", json=_user(1))
        assert resp.status_code in (400, 409, 422), resp.text

    def test_register_password_without_digit_fails(self, client):
        data = _user(99)
        data["password"] = "NoDigitsHere"
        resp = client.post("/auth/register", json=data)
        assert resp.status_code == 422, resp.text

    def test_register_password_too_short_fails(self, client):
        data = _user(99)
        data["password"] = "Ab1"
        resp = client.post("/auth/register", json=data)
        assert resp.status_code == 422, resp.text

    def test_register_username_too_short_fails(self, client):
        data = _user(99)
        data["username"] = "ab"
        resp = client.post("/auth/register", json=data)
        assert resp.status_code == 422, resp.text

    def test_register_username_too_long_fails(self, client):
        data = _user(99)
        data["username"] = "a" * 33
        resp = client.post("/auth/register", json=data)
        assert resp.status_code == 422, resp.text

    def test_register_invalid_email_fails(self, client):
        data = _user(99)
        data["email"] = "not-an-email"
        resp = client.post("/auth/register", json=data)
        assert resp.status_code == 422, resp.text


# ─────────────────────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_success(self, client, tokens):
        data = _user(1)
        resp = client.post("/auth/login", json={"email": data["email"], "password": data["password"]})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 10

    def test_login_wrong_password_fails(self, client, tokens):
        data = _user(1)
        resp = client.post("/auth/login", json={"email": data["email"], "password": "WrongPass999"})
        assert resp.status_code in (400, 401), resp.text

    def test_login_unknown_email_fails(self, client):
        resp = client.post("/auth/login", json={"email": "ghost@nowhere.com", "password": "TestPass123"})
        assert resp.status_code in (400, 401, 404), resp.text

    def test_login_invalid_email_format_fails(self, client):
        resp = client.post("/auth/login", json={"email": "not-an-email", "password": "TestPass123"})
        assert resp.status_code == 422, resp.text


# ─────────────────────────────────────────────────────────────────────────────
# Posts
# ─────────────────────────────────────────────────────────────────────────────

class TestPosts:
    def test_create_post_returns_expected_fields(self, client, tokens):
        resp = client.post("/posts/", json={"content": "Hello world!"}, headers=_auth(tokens[1]))
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["content"] == "Hello world!"
        assert "id" in body
        assert "user_id" in body
        assert "created_at" in body

    def test_multiple_users_can_post(self, client, tokens):
        for n, text in [(1, "Post A"), (2, "Post B"), (3, "Post C")]:
            resp = client.post("/posts/", json={"content": text}, headers=_auth(tokens[n]))
            assert resp.status_code == 201, resp.text

    def test_create_post_unauthenticated_fails(self, client):
        resp = client.post("/posts/", json={"content": "No token"})
        assert resp.status_code == 401, resp.text

    def test_create_post_empty_content_fails(self, client, tokens):
        resp = client.post("/posts/", json={"content": ""}, headers=_auth(tokens[1]))
        assert resp.status_code == 422, resp.text

    def test_create_post_content_over_limit_fails(self, client, tokens):
        resp = client.post("/posts/", json={"content": "x" * 281}, headers=_auth(tokens[1]))
        assert resp.status_code == 422, resp.text

    def test_create_post_max_length_succeeds(self, client, tokens):
        resp = client.post("/posts/", json={"content": "y" * 280}, headers=_auth(tokens[1]))
        assert resp.status_code == 201, resp.text

    def test_delete_own_post(self, client, tokens):
        create = client.post("/posts/", json={"content": "Delete me"}, headers=_auth(tokens[1]))
        assert create.status_code == 201
        post_id = create.json()["id"]

        delete = client.delete(f"/posts/{post_id}", headers=_auth(tokens[1]))
        assert delete.status_code == 204, delete.text

    def test_delete_another_users_post_fails(self, client, tokens):
        create = client.post("/posts/", json={"content": "Mine!"}, headers=_auth(tokens[1]))
        assert create.status_code == 201
        post_id = create.json()["id"]

        delete = client.delete(f"/posts/{post_id}", headers=_auth(tokens[2]))
        assert delete.status_code in (403, 404), delete.text

    def test_delete_nonexistent_post_fails(self, client, tokens):
        resp = client.delete("/posts/999999999", headers=_auth(tokens[1]))
        assert resp.status_code in (403, 404), resp.text

    def test_delete_unauthenticated_fails(self, client, tokens):
        create = client.post("/posts/", json={"content": "Temp"}, headers=_auth(tokens[1]))
        assert create.status_code == 201
        post_id = create.json()["id"]
        resp = client.delete(f"/posts/{post_id}")
        assert resp.status_code == 401, resp.text


# ─────────────────────────────────────────────────────────────────────────────
# Likes
# ─────────────────────────────────────────────────────────────────────────────

class TestLikes:
    @pytest.fixture(scope="class")
    def likeable_post(self, client, tokens):
        resp = client.post("/posts/", json={"content": "Like me!"}, headers=_auth(tokens[1]))
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_like_post(self, client, tokens, likeable_post):
        resp = client.post(f"/posts/{likeable_post}/like", headers=_auth(tokens[2]))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["liked"] is True
        assert body["post_id"] == likeable_post
        assert body["likes_count"] >= 1

    def test_like_increments_count(self, client, tokens, likeable_post):
        resp = client.post(f"/posts/{likeable_post}/like", headers=_auth(tokens[3]))
        assert resp.status_code == 200, resp.text
        assert resp.json()["likes_count"] >= 2

    def test_like_same_post_twice_idempotent(self, client, tokens, likeable_post):
        """Liking the same post twice must not raise a 5xx."""
        client.post(f"/posts/{likeable_post}/like", headers=_auth(tokens[2]))
        resp = client.post(f"/posts/{likeable_post}/like", headers=_auth(tokens[2]))
        assert resp.status_code in (200, 400, 409), resp.text

    def test_unlike_post(self, client, tokens, likeable_post):
        client.post(f"/posts/{likeable_post}/like", headers=_auth(tokens[2]))
        resp = client.delete(f"/posts/{likeable_post}/like", headers=_auth(tokens[2]))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["liked"] is False
        assert body["post_id"] == likeable_post

    def test_like_then_unlike_then_like_again(self, client, tokens, likeable_post):
        client.post(f"/posts/{likeable_post}/like", headers=_auth(tokens[1]))
        client.delete(f"/posts/{likeable_post}/like", headers=_auth(tokens[1]))
        resp = client.post(f"/posts/{likeable_post}/like", headers=_auth(tokens[1]))
        assert resp.status_code == 200, resp.text
        assert resp.json()["liked"] is True

    def test_like_unauthenticated_fails(self, client, likeable_post):
        resp = client.post(f"/posts/{likeable_post}/like")
        assert resp.status_code == 401, resp.text

    def test_unlike_unauthenticated_fails(self, client, likeable_post):
        resp = client.delete(f"/posts/{likeable_post}/like")
        assert resp.status_code == 401, resp.text

    def test_like_nonexistent_post_fails(self, client, tokens):
        resp = client.post("/posts/999999999/like", headers=_auth(tokens[1]))
        assert resp.status_code in (400, 404), resp.text


# ─────────────────────────────────────────────────────────────────────────────
# Replies
# ─────────────────────────────────────────────────────────────────────────────

class TestReplies:
    @pytest.fixture(scope="class")
    def reply_post(self, client, tokens):
        resp = client.post("/posts/", json={"content": "Reply to me!"}, headers=_auth(tokens[1]))
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_create_reply(self, client, tokens, reply_post):
        resp = client.post(
            f"/posts/{reply_post}/replies/",
            json={"content": "Great post!"},
            headers=_auth(tokens[2]),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["content"] == "Great post!"
        assert body["post_id"] == reply_post
        assert "id" in body
        assert "user_id" in body
        assert "created_at" in body

    def test_multiple_users_can_reply(self, client, tokens, reply_post):
        for n, text in [(1, "Author replies"), (3, "User 3 chimes in"), (2, "And again!")]:
            resp = client.post(
                f"/posts/{reply_post}/replies/",
                json={"content": text},
                headers=_auth(tokens[n]),
            )
            assert resp.status_code == 201, resp.text

    def test_get_replies_returns_list(self, client, tokens, reply_post):
        resp = client.get(f"/posts/{reply_post}/replies/", headers=_auth(tokens[1]))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "replies" in body
        assert isinstance(body["replies"], list)
        assert len(body["replies"]) >= 1

    def test_reply_empty_content_fails(self, client, tokens, reply_post):
        resp = client.post(
            f"/posts/{reply_post}/replies/",
            json={"content": ""},
            headers=_auth(tokens[1]),
        )
        assert resp.status_code == 422, resp.text

    def test_reply_content_over_limit_fails(self, client, tokens, reply_post):
        resp = client.post(
            f"/posts/{reply_post}/replies/",
            json={"content": "z" * 281},
            headers=_auth(tokens[1]),
        )
        assert resp.status_code == 422, resp.text

    def test_reply_unauthenticated_fails(self, client, reply_post):
        resp = client.post(f"/posts/{reply_post}/replies/", json={"content": "no auth"})
        assert resp.status_code == 401, resp.text

    def test_reply_to_nonexistent_post_fails(self, client, tokens):
        resp = client.post(
            "/posts/999999999/replies/",
            json={"content": "ghost"},
            headers=_auth(tokens[1]),
        )
        assert resp.status_code in (400, 404), resp.text

    def test_get_replies_unauthenticated_fails(self, client, reply_post):
        resp = client.get(f"/posts/{reply_post}/replies/")
        assert resp.status_code == 401, resp.text


# ─────────────────────────────────────────────────────────────────────────────
# Feed
# ─────────────────────────────────────────────────────────────────────────────

class TestFeed:
    def test_feed_returns_expected_shape(self, client, tokens):
        resp = client.get("/feed/", headers=_auth(tokens[1]))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "posts" in body
        assert isinstance(body["posts"], list)

    def test_feed_contains_created_posts(self, client, tokens):
        client.post("/posts/", json={"content": "Feed visibility test"}, headers=_auth(tokens[1]))
        resp = client.get("/feed/", headers=_auth(tokens[1]))
        assert resp.status_code == 200
        contents = [p["content"] for p in resp.json()["posts"]]
        assert "Feed visibility test" in contents

    def test_feed_limit_respected(self, client, tokens):
        for i in range(3):
            client.post("/posts/", json={"content": f"Limit test {i}"}, headers=_auth(tokens[2]))
        resp = client.get("/feed/?limit=2", headers=_auth(tokens[1]))
        assert resp.status_code == 200
        assert len(resp.json()["posts"]) <= 2

    def test_feed_cursor_pagination(self, client, tokens):
        for i in range(4):
            client.post("/posts/", json={"content": f"Page {i}"}, headers=_auth(tokens[3]))
        page1 = client.get("/feed/?limit=2", headers=_auth(tokens[1]))
        assert page1.status_code == 200
        assert len(page1.json()["posts"]) <= 2
        cursor = page1.json().get("next_cursor")
        if cursor:
            page2 = client.get(f"/feed/?limit=2&cursor={cursor}", headers=_auth(tokens[1]))
            assert page2.status_code == 200
            assert "posts" in page2.json()
            assert len(page2.json()["posts"]) <= 2

    def test_feed_unauthenticated_fails(self, client):
        resp = client.get("/feed/")
        assert resp.status_code == 401, resp.text

    def test_feed_limit_zero_fails(self, client, tokens):
        resp = client.get("/feed/?limit=0", headers=_auth(tokens[1]))
        assert resp.status_code == 422, resp.text

    def test_feed_limit_max_allowed(self, client, tokens):
        resp = client.get("/feed/?limit=100", headers=_auth(tokens[1]))
        assert resp.status_code == 200, resp.text

    def test_feed_limit_exceeds_max_fails(self, client, tokens):
        resp = client.get("/feed/?limit=101", headers=_auth(tokens[1]))
        assert resp.status_code == 422, resp.text

    def test_feed_post_fields(self, client, tokens):
        client.post("/posts/", json={"content": "Field check post"}, headers=_auth(tokens[1]))
        resp = client.get("/feed/?limit=10", headers=_auth(tokens[1]))
        assert resp.status_code == 200
        for post in resp.json()["posts"]:
            assert "id" in post
            assert "user_id" in post
            assert "content" in post
            assert "created_at" in post
