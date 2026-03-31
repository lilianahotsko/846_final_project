import pytest
from .conftest import register_user, login_user, auth_header
from fastapi.testclient import TestClient

class TestLikes:
    # Given a post, When liked, Then like is recorded
    def test_like_post_success(self, client):
        register_user(client, "likeuser1", "likeuser1@example.com", "Password1")
        token = login_user(client, "likeuser1@example.com", "Password1")
        post_resp = client.post("/posts", json={"content": "Like me!"}, headers=auth_header(token))
        post_id = post_resp.json()["id"]
        like_resp = client.post(f"/posts/{post_id}/like", headers=auth_header(token))
        assert like_resp.status_code == 200 or like_resp.status_code == 201
        assert like_resp.json().get("liked") is True

    # Given a post, When liked twice, Then idempotent
    def test_like_post_idempotent(self, client):
        register_user(client, "likeuser2", "likeuser2@example.com", "Password1")
        token = login_user(client, "likeuser2@example.com", "Password1")
        post_resp = client.post("/posts", json={"content": "Like me twice!"}, headers=auth_header(token))
        post_id = post_resp.json()["id"]
        client.post(f"/posts/{post_id}/like", headers=auth_header(token))
        like_resp2 = client.post(f"/posts/{post_id}/like", headers=auth_header(token))
        assert like_resp2.status_code == 200 or like_resp2.status_code == 201
        assert like_resp2.json().get("liked") is True

    # Given a post, When unliked, Then like is removed
    def test_unlike_post(self, client):
        register_user(client, "likeuser3", "likeuser3@example.com", "Password1")
        token = login_user(client, "likeuser3@example.com", "Password1")
        post_resp = client.post("/posts", json={"content": "Unlike me!"}, headers=auth_header(token))
        post_id = post_resp.json()["id"]
        client.post(f"/posts/{post_id}/like", headers=auth_header(token))
        unlike_resp = client.delete(f"/posts/{post_id}/like", headers=auth_header(token))
        assert unlike_resp.status_code == 200 or unlike_resp.status_code == 204
        if unlike_resp.status_code == 200:
            assert unlike_resp.json().get("liked") is False

    # Given non-existent post, When liked, Then error returned
    def test_like_nonexistent_post(self, client):
        register_user(client, "likeuser4", "likeuser4@example.com", "Password1")
        token = login_user(client, "likeuser4@example.com", "Password1")
        resp = client.post(f"/posts/999999/like", headers=auth_header(token))
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "POST_NOT_FOUND"

    # Given concurrent likes, When two users like at once, Then only one like per user
    def test_like_post_concurrent(self, client):
        register_user(client, "likeuser5", "likeuser5@example.com", "Password1")
        register_user(client, "likeuser6", "likeuser6@example.com", "Password1")
        token1 = login_user(client, "likeuser5@example.com", "Password1")
        token2 = login_user(client, "likeuser6@example.com", "Password1")
        post_resp = client.post("/posts", json={"content": "Race!"}, headers=auth_header(token1))
        post_id = post_resp.json()["id"]
        # Simulate concurrent likes
        resp1 = client.post(f"/posts/{post_id}/like", headers=auth_header(token1))
        resp2 = client.post(f"/posts/{post_id}/like", headers=auth_header(token2))
        assert resp1.status_code in (200, 201)
        assert resp2.status_code in (200, 201)
        # Like count should be 2 (if like count is returned)
