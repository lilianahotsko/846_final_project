import requests
import json
import logging
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)

def log_response(action, response):
    try:
        data = response.json()
    except Exception:
        data = response.text
    logging.info(f"ACTION: {action} | STATUS: {response.status_code} | RESPONSE: {json.dumps(data, indent=2) if isinstance(data, dict) else data}")

def test_register():
    url = f"{API_URL}/auth/register"
    payload = {
        "username": f"testuser_{datetime.utcnow().timestamp():.0f}",
        "email": f"testuser_{datetime.utcnow().timestamp():.0f}@example.com",
        "password": "Testpass123",
        "bio": "Test bio",
        "avatar_url": "https://example.com/avatar.png"
    }
    response = requests.post(url, json=payload)
    log_response("register", response)
    return response

def test_login(email, password):
    url = f"{API_URL}/auth/login"
    payload = {"email": email, "password": password}
    response = requests.post(url, json=payload)
    log_response("login", response)
    if response.status_code == 200:
        return response.json()["access_token"]

    import requests
    import logging
    from datetime import datetime, timezone

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s ACTION: %(action)s | STATUS: %(status)s | RESPONSE: %(response)s")

    def log(action, status, response):
        logging.info("", extra={"action": action, "status": status, "response": response})

    def main():
        base_url = "http://127.0.0.1:8000"
        register_url = f"{base_url}/auth/register"
        login_url = f"{base_url}/auth/login"
        now_ts = datetime.now(timezone.utc).timestamp()
        user_data = {
            "username": f"testuser_{now_ts:.0f}",
            "email": f"testuser_{now_ts:.0f}@example.com",
            "password": "Testpass123",
            "bio": "Test bio",
            "avatar_url": "https://example.com/avatar.png"
        }
        # Register
        r = requests.post(register_url, json=user_data)
        log("register", r.status_code, r.text if r.status_code != 200 and r.status_code != 201 else r.json())
        if r.status_code != 200 and r.status_code != 201:
            logging.error("Registration failed.")
            return
        # Login
        r = requests.post(login_url, json={"email": user_data["email"], "password": user_data["password"]})
        log("login", r.status_code, r.text if r.status_code != 200 else r.json())
        if r.status_code != 200:
            logging.error("Login failed.")
            return
        token = r.json().get("access_token")
        print("Access token:", token)

    if __name__ == "__main__":
        main()
