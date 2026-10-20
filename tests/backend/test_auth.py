"""Tests for administrator authentication, tokens, and login rate limiting."""

from __future__ import annotations

from app.core.config import get_settings
from app.models.enums import Role

settings = get_settings()


def test_login_success_returns_tokens(client, make_admin):
    _, email, password = make_admin()
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["expires_in"] == settings.access_token_minutes * 60


def test_login_wrong_password_rejected(client, make_admin):
    _, email, _ = make_admin()
    resp = client.post("/auth/login", json={"email": email, "password": "nope"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


def test_login_unknown_email_same_message(client):
    # No such admin; message must be identical to wrong-password (no enumeration).
    resp = client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "whatever"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_token(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "owner"
    assert "manage_admins" in body["permissions"]


def test_me_rejects_garbage_token(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_refresh_issues_new_access_token(client, make_admin):
    _, email, password = make_admin()
    login = client.post(
        "/auth/login", json={"email": email, "password": password}
    ).json()
    resp = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert resp.status_code == 200
    new_access = resp.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200


def test_refresh_rejects_access_token(client, make_admin):
    # An access token must not be accepted where a refresh token is required.
    _, email, password = make_admin()
    login = client.post(
        "/auth/login", json={"email": email, "password": password}
    ).json()
    resp = client.post("/auth/refresh", json={"refresh_token": login["access_token"]})
    assert resp.status_code == 401


def test_login_rate_limited(client, make_admin):
    _, email, _ = make_admin()
    # Exhaust the allowed attempts with wrong passwords.
    for _ in range(settings.login_max_attempts):
        r = client.post("/auth/login", json={"email": email, "password": "wrong"})
        assert r.status_code == 401
    # The next attempt is blocked regardless of correctness.
    blocked = client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_login_validation_error(client):
    # Missing password field -> 422 from request validation.
    resp = client.post("/auth/login", json={"email": "a@b.com"})
    assert resp.status_code == 422
