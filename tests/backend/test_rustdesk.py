"""Tests for RustDesk credential reporting and retrieval."""

from __future__ import annotations

from app.models.enums import Role

NEW_DEVICE = {"name": "RD Laptop", "os_type": "windows", "device_type": "laptop"}


def _enroll(client, headers) -> tuple[str, str]:
    created = client.post("/devices", json=NEW_DEVICE, headers=headers).json()
    uid = created["device"]["device_uid"]
    secret = created["enrollment_secret"]
    token = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    ).json()["device_token"]
    return uid, token


def _dev(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_report_requires_device_token(client):
    resp = client.post("/agent/rustdesk", json={"rustdesk_id": "1", "password": "p"})
    assert resp.status_code == 401


def test_not_reported_returns_409(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, _ = _enroll(client, headers)
    assert client.get(f"/devices/{uid}/rustdesk", headers=headers).status_code == 409


def test_retrieve_requires_permission(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, _ = _enroll(client, owner)
    viewer = auth_headers(email="v@example.com", role=Role.VIEWER)
    assert client.get(f"/devices/{uid}/rustdesk", headers=viewer).status_code == 403


def test_report_and_retrieve(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, token = _enroll(client, owner)

    up = client.post(
        "/agent/rustdesk",
        json={"rustdesk_id": "123456789", "password": "s3cret-pw"},
        headers=_dev(token),
    )
    assert up.status_code == 204

    # The id shows on the device; the password round-trips (decrypted) for admins.
    device = client.get(f"/devices/{uid}", headers=owner).json()
    assert device["rustdesk_id"] == "123456789"

    creds = client.get(f"/devices/{uid}/rustdesk", headers=owner).json()
    assert creds["rustdesk_id"] == "123456789"
    assert creds["password"] == "s3cret-pw"
    assert creds["enabled"] is False  # RUSTDESK_HOST not set in tests


def test_directives_include_rustdesk_block(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    _, token = _enroll(client, owner)
    directives = client.get("/agent/directives", headers=_dev(token)).json()
    assert "rustdesk" in directives
    assert directives["rustdesk"]["enabled"] is False
