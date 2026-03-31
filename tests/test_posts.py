import pytest
from .conftest import register_user, login_user, auth_header
from fastapi.testclient import TestClient

class TestPosts:
    # Given valid data, When creating a post, Then post is created
    def test_create_post_valid(self, client):
        register_user(client, "postuser1", "postuser1@example.com", "Password1")
        token = login_user(client, "postuser1@example.com", "Password1")
        resp = client.post("/posts", json={"content": "Hello world!"}, headers=auth_header(token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["content"] == "Hello world!"
        assert data["user_id"]
        assert data["id"]
        assert data["created_at"]

    # Given >280 chars, When creating a post, Then error returned
    def test_create_post_too_long(self, client):
        register_user(client, "postuser2", "postuser2@example.com", "Password1")
        token = login_user(client, "postuser2@example.com", "Password1")
        content = "a" * 281
        resp = client.post("/posts", json={"content": content}, headers=auth_header(token))
        assert resp.status_code == 400 or resp.status_code == 422

    # Given exactly 280 chars, When creating a post, Then post is created
    def test_create_post_280_chars(self, client):
        register_user(client, "postuser3", "postuser3@example.com", "Password1")
        token = login_user(client, "postuser3@example.com", "Password1")
        content = "b" * 280
        resp = client.post("/posts", json={"content": content}, headers=auth_header(token))
        assert resp.status_code == 201
        assert resp.json()["content"] == content

    # Given own post, When deleting, Then post is deleted
    def test_delete_own_post(self, client):
        register_user(client, "postuser4", "postuser4@example.com", "Password1")
        token = login_user(client, "postuser4@example.com", "Password1")
        resp = client.post("/posts", json={"content": "To be deleted"}, headers=auth_header(token))
        post_id = resp.json()["id"]
        del_resp = client.delete(f"/posts/{post_id}", headers=auth_header(token))
        assert del_resp.status_code == 204

    # Given another user's post, When deleting, Then forbidden
    def test_delete_another_users_post(self, client):
        register_user(client, "postuser5", "postuser5@example.com", "Password1")
        register_user(client, "postuser6", "postuser6@example.com", "Password1")
        token1 = login_user(client, "postuser5@example.com", "Password1")
        token2 = login_user(client, "postuser6@example.com", "Password1")
        resp = client.post("/posts", json={"content": "Not yours"}, headers=auth_header(token1))
        post_id = resp.json()["id"]
        del_resp = client.delete(f"/posts/{post_id}", headers=auth_header(token2))
        assert del_resp.status_code == 403 or del_resp.status_code == 404

    # Given empty feed, When fetching, Then empty list
    def test_feed_empty(self, client):
        register_user(client, "postuser7", "postuser7@example.com", "Password1")
        token = login_user(client, "postuser7@example.com", "Password1")
        resp = client.get("/feed", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["posts"] == []

    # Given multiple posts, When paginating, Then correct cursor behavior
    def test_feed_pagination(self, client):
        register_user(client, "postuser8", "postuser8@example.com", "Password1")
        token = login_user(client, "postuser8@example.com", "Password1")
        for i in range(25):
            client.post("/posts", json={"content": f"Post {i}"}, headers=auth_header(token))
        resp1 = client.get("/feed?limit=10", headers=auth_header(token))
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert len(data1["posts"]) == 10
        next_cursor = data1["next_cursor"]
        resp2 = client.get(f"/feed?limit=10&cursor={next_cursor}", headers=auth_header(token))
        data2 = resp2.json()
        assert len(data2["posts"]) == 10
        assert data1["posts"][0]["id"] != data2["posts"][0]["id"]
