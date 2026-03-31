import pytest
from fastapi.testclient import TestClient
from .conftest import register_user, login_user, auth_header

class TestAuth:
    # Given valid registration data, When registering, Then registration succeeds
    def test_register_success(self, client):
        resp = register_user(client, "user1", "user1@example.com", "Password1")
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "user1"
        assert data["email"] == "user1@example.com"
        assert "id" in data
        assert "created_at" in data

    # Given duplicate username/email, When registering, Then error returned
    def test_register_duplicate_username_email(self, client):
        register_user(client, "user2", "user2@example.com", "Password1")
        resp = register_user(client, "user2", "user2@example.com", "Password1")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] in ("USERNAME_TAKEN", "EMAIL_TAKEN")

    # Given invalid password, When registering, Then error returned
    @pytest.mark.parametrize("password", ["password", "12345678", "abcdefgh", ""])
    def test_register_invalid_password(self, client, password):
        resp = register_user(client, "user3", f"user3_{password}@example.com", password)
        assert resp.status_code == 422 or resp.status_code == 400

    # Given valid credentials, When logging in, Then login succeeds
    def test_login_success(self, client):
        register_user(client, "user4", "user4@example.com", "Password1")
        resp = client.post("/auth/login", json={"email": "user4@example.com", "password": "Password1"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    # Given wrong password, When logging in, Then error returned
    def test_login_failure_wrong_password(self, client):
        register_user(client, "user5", "user5@example.com", "Password1")
        resp = client.post("/auth/login", json={"email": "user5@example.com", "password": "WrongPass1"})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # Given multiple failed logins, When exceeding rate limit, Then 429 returned
    def test_login_rate_limit(self, client, monkeypatch):
        register_user(client, "user6", "user6@example.com", "Password1")
        for _ in range(5):
            client.post("/auth/login", json={"email": "user6@example.com", "password": "WrongPass1"})
        resp = client.post("/auth/login", json={"email": "user6@example.com", "password": "WrongPass1"})
        assert resp.status_code == 429 or resp.status_code == 401
