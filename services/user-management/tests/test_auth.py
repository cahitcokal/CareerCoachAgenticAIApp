import itertools

from conftest import auth

_counter = itertools.count()


def _register(client, email=None, password="password123", name="Test User"):
    email = email or f"user{next(_counter)}@example.com"
    resp = client.post("/auth/register", json={
        "full_name": name, "email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_register_login_me(client):
    data = _register(client)
    assert data["access_token"]
    assert data["user"]["email"].endswith("@example.com")

    token = data["access_token"]
    me = client.get("/auth/me", headers=auth(token))
    assert me.status_code == 200
    assert me.json()["id"] == data["user"]["id"]

    login = client.post("/auth/login", json={
        "email": data["user"]["email"], "password": "password123"})
    assert login.status_code == 200


def test_register_duplicate_email(client):
    email = f"dup{next(_counter)}@example.com"
    _register(client, email=email)
    resp = client.post("/auth/register", json={
        "full_name": "X", "email": email, "password": "password123"})
    assert resp.status_code == 409


def test_login_wrong_password(client):
    data = _register(client)
    resp = client.post("/auth/login", json={
        "email": data["user"]["email"], "password": "wrong-password"})
    assert resp.status_code == 401


def test_unauthenticated_rejected(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_change_password_flow(client):
    data = _register(client)
    token = data["access_token"]
    resp = client.post("/auth/change-password", headers=auth(token), json={
        "current_password": "password123", "new_password": "new-password-456"})
    assert resp.status_code == 204
    login = client.post("/auth/login", json={
        "email": data["user"]["email"], "password": "new-password-456"})
    assert login.status_code == 200


def test_forgot_reset_password(client, capsys):
    data = _register(client)
    email = data["user"]["email"]
    resp = client.post("/auth/forgot-password", json={"email": email})
    assert resp.status_code == 202
    # Token is printed to stdout in dev mode.
    out = capsys.readouterr().out
    token = out.split("token for user")[-1].split(":")[-1].strip()
    assert token
    reset = client.post("/auth/reset-password", json={
        "token": token, "new_password": "reset-password-789"})
    assert reset.status_code == 204
    login = client.post("/auth/login", json={"email": email, "password": "reset-password-789"})
    assert login.status_code == 200


def test_update_me(client):
    data = _register(client)
    resp = client.patch("/auth/me", headers=auth(data["access_token"]),
                        json={"full_name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "New Name"


def test_internal_endpoints_require_key(client):
    assert client.get("/internal/users/1").status_code == 403
    resp = client.get("/internal/users/1", headers={"X-Internal-Key": "test-internal"})
    assert resp.status_code == 200
