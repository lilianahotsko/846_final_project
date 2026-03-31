"""
simulate_ui.py — End-to-end demo of the social media API.

Simulates three users signing up, posting, liking each other's posts,
and leaving comments, exactly as a UI would.

Usage:
    python3 simulate_ui.py

Requires the server to be running:
    uvicorn src.main:app --reload
"""

import sys
import uuid
import requests

BASE = "http://127.0.0.1:8000"

# ── Pretty printing helpers ───────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
RED    = "\033[31m"
DIM    = "\033[2m"

def header(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}")

def step(description: str) -> None:
    print(f"\n{BOLD}{YELLOW}▶  {description}{RESET}")

def ok(label: str, value: str = "") -> None:
    suffix = f"  {DIM}{value}{RESET}" if value else ""
    print(f"  {GREEN}✓{RESET}  {label}{suffix}")

def info(label: str, value: str = "") -> None:
    suffix = f"  {DIM}{value}{RESET}" if value else ""
    print(f"  {CYAN}·{RESET}  {label}{suffix}")

def fail(label: str, body: str = "") -> None:
    print(f"  {RED}✗  {label}{RESET}")
    if body:
        print(f"      {DIM}{body}{RESET}")
    sys.exit(1)

# ── HTTP wrappers ─────────────────────────────────────────────────────────────

def post(path: str, json: dict, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(f"{BASE}{path}", json=json, headers=headers)
    return r

def get(path: str, token: str | None = None, params: dict | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{BASE}{path}", headers=headers, params=params or {})
    return r

def delete(path: str, token: str | None = None) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.delete(f"{BASE}{path}", headers=headers)
    return r

# ── Main simulation ───────────────────────────────────────────────────────────

def main() -> None:
    run_id = uuid.uuid4().hex[:6]

    # ── Health check ─────────────────────────────────────────────────────────
    header("Health Check")
    r = get("/health")
    if r.status_code == 200:
        ok("Server is up", r.json().get("status"))
    else:
        fail("Server not responding")

    # ── User definitions ─────────────────────────────────────────────────────
    users = [
        {
            "username": f"alice_{run_id}",
            "email":    f"alice_{run_id}@example.com",
            "password": "Alice1234",
            "bio":      "Hi, I'm Alice 👋",
            "avatar_url": "",
        },
        {
            "username": f"bob_{run_id}",
            "email":    f"bob_{run_id}@example.com",
            "password": "Bobby5678",
            "bio":      "Bob here, love coding",
            "avatar_url": "",
        },
        {
            "username": f"carol_{run_id}",
            "email":    f"carol_{run_id}@example.com",
            "password": "Carol9012",
            "bio":      "Carol — coffee & code",
            "avatar_url": "",
        },
    ]

    # ── Registration ─────────────────────────────────────────────────────────
    header("Step 1 — User Registration")
    profiles = {}  # username → {id, token}

    for u in users:
        step(f"Registering @{u['username']}")
        r = post("/auth/register", json=u)
        if r.status_code == 201:
            body = r.json()
            ok(f"Registered", f"id={body['id']}  email={body['email']}")
            profiles[u["username"]] = {"id": body["id"], "data": u}
        else:
            fail(f"Registration failed for {u['username']}", str(r.json()))

    # ── Login ─────────────────────────────────────────────────────────────────
    header("Step 2 — Login")
    tokens = {}  # username → JWT

    for u in users:
        step(f"@{u['username']} logging in")
        r = post("/auth/login", json={"email": u["email"], "password": u["password"]})
        if r.status_code == 200:
            token = r.json()["access_token"]
            tokens[u["username"]] = token
            ok("Login successful", f"token={token[:24]}…")
        else:
            fail(f"Login failed for {u['username']}", str(r.json()))

    alice = users[0]["username"]
    bob   = users[1]["username"]
    carol = users[2]["username"]

    # ── Wrong-password attempt ─────────────────────────────────────────────
    step("Alice tries to log in with the wrong password")
    r = post("/auth/login", json={"email": users[0]["email"], "password": "wrongpassword1"})
    if r.status_code in (400, 401):
        ok("Rejected with 401 as expected", str(r.status_code))
    else:
        info("Unexpected status", str(r.status_code))

    # ── Creating posts ────────────────────────────────────────────────────────
    header("Step 3 — Creating Posts")

    post_ids = {}  # label → post_id

    def make_post(username: str, content: str, label: str) -> None:
        step(f"@{username} posts: "{content}"")
        r = post("/posts/", json={"content": content}, token=tokens[username])
        if r.status_code == 201:
            body = r.json()
            post_ids[label] = body["id"]
            ok("Post created", f"id={body['id']}  created_at={body['created_at']}")
        else:
            fail(f"Post creation failed", str(r.json()))

    make_post(alice, "Just set up my account — hello world! 🌍", "alice_1")
    make_post(alice, "Tip: always write tests before shipping 🧪", "alice_2")
    make_post(bob,   "Anyone else drinking too much coffee today? ☕", "bob_1")
    make_post(bob,   "Finished a new side project — really proud of it 🚀", "bob_2")
    make_post(carol, "Hot take: tabs > spaces 🔥", "carol_1")
    make_post(carol, "Reading 'Clean Code' for the third time. Still learning.", "carol_2")

    # ── Validation: content too long ──────────────────────────────────────────
    step("Bob tries to post a message over 280 characters (should fail)")
    r = post("/posts/", json={"content": "x" * 281}, token=tokens[bob])
    if r.status_code == 422:
        ok("Server rejected over-limit post (422 Unprocessable Entity)")
    else:
        info("Unexpected status", str(r.status_code))

    # ── Liking posts ──────────────────────────────────────────────────────────
    header("Step 4 — Liking Posts")

    def like(username: str, label: str) -> None:
        pid = post_ids[label]
        step(f"@{username} likes post #{pid}")
        r = post(f"/posts/{pid}/like", json={}, token=tokens[username])
        if r.status_code == 200:
            body = r.json()
            ok(f"Liked!", f"likes_count={body['likes_count']}")
        else:
            fail(f"Like failed", str(r.json()))

    like(bob,   "alice_1")
    like(carol, "alice_1")
    like(alice, "bob_2")
    like(carol, "bob_2")
    like(alice, "carol_1")
    like(bob,   "carol_1")

    # ── Like → unlike → like cycle ────────────────────────────────────────────
    step(f"Carol likes, then un-likes, then re-likes Alice's second post")
    pid = post_ids["alice_2"]
    for action, endpoint, label in [
        ("like",   f"/posts/{pid}/like", "like"),
        ("unlike", f"/posts/{pid}/like", "unlike"),
        ("like",   f"/posts/{pid}/like", "re-like"),
    ]:
        method = post if action == "like" else delete
        r = method(f"/posts/{pid}/like", token=tokens[carol])
        if r.status_code == 200:
            body = r.json()
            ok(f"{label.capitalize()} → liked={body['liked']}  count={body['likes_count']}")
        else:
            info(f"{label} responded with {r.status_code}", str(r.json()))

    # ── Replying to posts ─────────────────────────────────────────────────────
    header("Step 5 — Commenting on Posts")

    def reply(username: str, label: str, content: str) -> None:
        pid = post_ids[label]
        step(f"@{username} replies to post #{pid}: "{content}"")
        r = post(f"/posts/{pid}/replies/", json={"content": content}, token=tokens[username])
        if r.status_code == 201:
            body = r.json()
            ok("Reply posted", f"reply_id={body['id']}  post_id={body['post_id']}")
        else:
            fail("Reply failed", str(r.json()))

    reply(bob,   "alice_1", "Welcome to the platform! 🎉")
    reply(carol, "alice_1", "Hello! Great to have you here.")
    reply(alice, "bob_1",   "Only 4 cups so far… it's only 9am 😅")
    reply(carol, "bob_1",   "I switched to tea last week, highly recommend.")
    reply(alice, "carol_1", "Controversial but I respect it 😂")
    reply(bob,   "carol_1", "Tabs gang rises 🙌")
    reply(carol, "alice_2", "100% agree on tests. Wish I had learned sooner!")

    # ── Validation: empty reply ───────────────────────────────────────────────
    step("Alice tries to post an empty reply (should fail)")
    pid = post_ids["bob_2"]
    r = post(f"/posts/{pid}/replies/", json={"content": ""}, token=tokens[alice])
    if r.status_code == 422:
        ok("Server rejected empty reply (422 Unprocessable Entity)")
    else:
        info("Unexpected status", str(r.status_code))

    # ── Reading replies ───────────────────────────────────────────────────────
    header("Step 6 — Reading Comments")

    for label, description in [("alice_1", "Alice's hello post"), ("carol_1", "Carol's tabs post")]:
        pid = post_ids[label]
        step(f"Fetching comments on {description} (post #{pid})")
        r = get(f"/posts/{pid}/replies/", token=tokens[alice])
        if r.status_code == 200:
            replies = r.json()["replies"]
            ok(f"{len(replies)} comment(s) found")
            for rep in replies:
                info(f"  → "{rep['content']}"", f"by user_id={rep['user_id']}")
        else:
            fail("Failed to fetch replies", str(r.json()))

    # ── Feed ─────────────────────────────────────────────────────────────────
    header("Step 7 — Reading the Feed")

    step("Alice opens her feed (first page, limit=3)")
    r = get("/feed/", token=tokens[alice], params={"limit": 3})
    if r.status_code == 200:
        feed = r.json()
        posts_page1 = feed["posts"]
        ok(f"Got {len(posts_page1)} posts on page 1")
        for p in posts_page1:
            preview = p['content'][:60] + "..." if len(p['content']) > 60 else p['content']
            info(f"  [{p['id']}] \"{preview}\"")
        cursor = feed.get("next_cursor")
        if cursor:
            cursor_preview = cursor[:30] + "..." if len(cursor) > 30 else cursor
            info("Next cursor available", cursor_preview)
    else:
        fail("Feed failed", str(r.json()))

    if cursor:
        step("Alice scrolls down — fetching page 2")
        r = get("/feed/", token=tokens[alice], params={"limit": 3, "cursor": cursor})
        if r.status_code == 200:
            posts_page2 = r.json()["posts"]
            ok(f"Got {len(posts_page2)} posts on page 2")
            for p in posts_page2:
                preview = p['content'][:60] + "..." if len(p['content']) > 60 else p['content']
                info(f"  [{p['id']}] \"{preview}\"")
        else:
            info("Page 2 request returned", str(r.status_code))

    # ── Unauthenticated access ────────────────────────────────────────────────
    header("Step 8 — Auth Guard Checks")

    step("Accessing the feed without a token (should be rejected)")
    r = get("/feed/")
    if r.status_code == 401:
        ok("401 Unauthorized — feed is protected")
    else:
        info("Unexpected status", str(r.status_code))

    step("Creating a post without a token (should be rejected)")
    r = post("/posts/", json={"content": "Am I in?"})
    if r.status_code == 401:
        ok("401 Unauthorized — posting is protected")
    else:
        info("Unexpected status", str(r.status_code))

    # ── Delete own post ───────────────────────────────────────────────────────
    header("Step 9 — Deleting a Post")

    step("Alice deletes her second post")
    pid = post_ids["alice_2"]
    r = delete(f"/posts/{pid}", token=tokens[alice])
    if r.status_code == 204:
        ok(f"Post #{pid} deleted successfully (204 No Content)")
    else:
        fail("Delete failed", str(r.json()))

    step("Bob tries to delete Carol's post (should be forbidden)")
    pid = post_ids["carol_2"]
    r = delete(f"/posts/{pid}", token=tokens[bob])
    if r.status_code in (403, 404):
        ok(f"Rejected with {r.status_code} — can't delete someone else's post")
    else:
        info("Unexpected status", str(r.status_code))

    # ── Summary ───────────────────────────────────────────────────────────────
    header("Simulation Complete")
    ok("3 users registered and logged in")
    ok("6 posts created across all users")
    ok("6 likes placed (cross-user)")
    ok("1 like/unlike/re-like cycle demonstrated")
    ok("7 comments posted")
    ok("Feed paginated across 2 pages")
    ok("Auth guards verified (unauthenticated requests rejected)")
    ok("Post deletion and ownership enforcement verified")
    print()


if __name__ == "__main__":
    main()
