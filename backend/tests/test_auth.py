VALID_USER = {
    "name": "Example User",
    "email": "user@example.com",
    "password": "password",
    "phone": "0500000000",
    "address": "Jerusalem",
    "roles": ["CLIENT", "VOLUNTEER"],
}


def _register(client, **overrides):
    payload = dict(VALID_USER)
    payload.update(overrides)
    return client.post("/api/auth/register", json=payload)


def _login(client, email=VALID_USER["email"], password=VALID_USER["password"]):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_register_valid_user(client):
    response = _register(client)

    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == VALID_USER["name"]
    assert body["email"] == VALID_USER["email"]
    assert body["roles"] == ["CLIENT", "VOLUNTEER"]
    assert "password" not in body
    assert "password_hash" not in body
    assert body["id"] >= 1


def test_reject_duplicate_email(client):
    first = _register(client)
    second = _register(client)

    assert first.status_code == 201
    assert second.status_code == 409
    assert "already registered" in second.get_json()["error"].lower()


def test_register_rejects_missing_role(client):
    response = _register(client, roles=[])

    assert response.status_code == 400
    assert "role" in response.get_json()["error"].lower()


def test_register_rejects_omitted_roles(client):
    payload = dict(VALID_USER)
    del payload["roles"]
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
    assert "roles" in response.get_json()["error"].lower()


def test_register_rejects_short_password(client):
    response = _register(client, password="short")

    assert response.status_code == 400
    assert "password" in response.get_json()["error"].lower()


def test_register_rejects_whitespace_only_name(client):
    response = _register(client, name="   ")

    assert response.status_code == 400
    assert "name" in response.get_json()["error"].lower()


def test_login_with_valid_credentials(client):
    _register(client)

    response = _login(client)

    assert response.status_code == 200
    body = response.get_json()
    assert body["access_token"]
    assert body["user"]["email"] == VALID_USER["email"]
    assert "password" not in body["user"]


def test_reject_invalid_credentials(client):
    _register(client)

    response = _login(client, password="wrong-password")

    assert response.status_code == 401
    assert "invalid" in response.get_json()["error"].lower()


def test_login_rejects_malformed_email(client):
    response = _login(client, email="not-an-email")

    assert response.status_code == 400
    error = response.get_json()["error"].lower()
    assert "email" in error
    assert "required" not in error or "not a valid email" in error or "invalid" in error


def test_login_rejects_missing_password(client):
    response = client.post(
        "/api/auth/login",
        json={"email": VALID_USER["email"]},
    )

    assert response.status_code == 400
    assert "password" in response.get_json()["error"].lower()


def test_protected_endpoint_without_auth_returns_401(client):
    response = client.get("/api/users/me")

    assert response.status_code == 401


def test_get_current_user_with_token(client):
    _register(client)
    token = _login(client).get_json()["access_token"]

    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["email"] == VALID_USER["email"]
    assert body["roles"] == ["CLIENT", "VOLUNTEER"]


def test_logout_then_token_is_rejected(client):
    _register(client)
    token = _login(client).get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200

    me = client.get("/api/users/me", headers=headers)
    assert me.status_code == 401
    assert me.get_json()["error"]
