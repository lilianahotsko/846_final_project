import pytest
from .conftest import register_user, login_user, auth_header
from fastapi.testclient import TestClient

class TestReplies:
    # Given a post, When replying, Then reply is created
    def test_reply_to_post_success(self, client):
        register_user(client, "replyuser1", "replyuser1@example.com", "Password1")
        token = login_user(client, "replyuser1@example.com", "Password1")
        post_resp = client.post("/posts", json={"content": "Reply to me!"}, headers=auth_header(token))
        post_id = post_resp.json()["id"]
        reply_resp = client.post(f"/posts/{post_id}/reply", json={"content": "First reply!"}, headers=auth_header(token))
        assert reply_resp.status_code == 201
        data = reply_resp.json()
        assert data["content"] == "First reply!"
        assert data["user_id"]
        assert data["post_id"] == post_id
        assert data["id"]
        assert data["created_at"]

    # Given >280 chars, When replying, Then error returned
    def test_reply_too_long(self, client):
        register_user(client, "replyuser2", "replyuser2@example.com", "Password1")
        token = login_user(client, "replyuser2@example.com", "Password1")
        post_resp = client.post("/posts", json={"content": "Reply to me!"}, headers=auth_header(token))
        post_id = post_resp.json()["id"]
        content = "a" * 281
        reply_resp = client.post(f"/posts/{post_id}/reply", json={"content": content}, headers=auth_header(token))
        assert reply_resp.status_code == 400 or reply_resp.status_code == 422

    # Given exactly 280 chars, When replying, Then reply is created
    def test_reply_280_chars(self, client):
        register_user(client, "replyuser3", "replyuser3@example.com", "Password1")
        token = login_user(client, "replyuser3@example.com", "Password1")
        post_resp = client.post("/posts", json={"content": "Reply to me!"}, headers=auth_header(token))
        post_id = post_resp.json()["id"]
        content = "b" * 280
        reply_resp = client.post(f"/posts/{post_id}/reply", json={"content": content}, headers=auth_header(token))
        assert reply_resp.status_code == 201
        assert reply_resp.json()["content"] == content

    # Given a reply, When replying to it, Then error returned
    def test_reply_to_reply_fails(self, client):
        register_user(client, "replyuser4", "replyuser4@example.com", "Password1")
        token = login_user(client, "replyuser4@example.com", "Password1")
        post_resp = client.post("/posts", json={"content": "Reply to me!"}, headers=auth_header(token))
        post_id = post_resp.json()["id"]
        reply_resp = client.post(f"/posts/{post_id}/reply", json={"content": "First reply!"}, headers=auth_header(token))
        reply_id = reply_resp.json()["id"]
        # Try to reply to a reply (should fail)
        fail_resp = client.post(f"/posts/{reply_id}/reply", json={"content": "Nested reply!"}, headers=auth_header(token))
        assert fail_resp.status_code == 400 or fail_resp.status_code == 404

    # Given a post with replies, When fetching, Then replies are ordered oldest to newest
    def test_fetch_replies_ordering(self, client):
        register_user(client, "replyuser5", "replyuser5@example.com", "Password1")
        token = login_user(client, "replyuser5@example.com", "Password1")
        post_resp = client.post("/posts", json={"content": "Reply to me!"}, headers=auth_header(token))
        post_id = post_resp.json()["id"]
        client.post(f"/posts/{post_id}/reply", json={"content": "First reply!"}, headers=auth_header(token))
        client.post(f"/posts/{post_id}/reply", json={"content": "Second reply!"}, headers=auth_header(token))
        replies_resp = client.get(f"/posts/{post_id}/replies", headers=auth_header(token))
        assert replies_resp.status_code == 200
        replies = replies_resp.json()["replies"]
        assert len(replies) == 2
        assert replies[0]["content"] == "First reply!"
        assert replies[1]["content"] == "Second reply!"

    # Given >50 replies/hour, When replying, Then rate limit error
    def test_reply_rate_limit(self, client):
        register_user(client, "replyuser6", "replyuser6@example.com", "Password1")
        token = login_user(client, "replyuser6@example.com", "Password1")
        post_resp = client.post("/posts", json={"content": "Reply to me!"}, headers=auth_header(token))
        post_id = post_resp.json()["id"]
        for i in range(50):
            client.post(f"/posts/{post_id}/reply", json={"content": f"Reply {i}"}, headers=auth_header(token))
        fail_resp = client.post(f"/posts/{post_id}/reply", json={"content": "Reply 51"}, headers=auth_header(token))
        assert fail_resp.status_code == 429
        assert fail_resp.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
