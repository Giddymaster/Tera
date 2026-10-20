"""Tests for device-agent enrollment, heartbeat, and token separation."""

from __future__ import annotations

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.enums import Role

settings = get_settings()

NEW_DEVICE = {"name": "Agent Laptop", "os_type": "windows", "device_type": "laptop"}


def _create_device(client, headers) -> tuple[str, str]:
    """Create a device via the admin API, returning (device_uid, secret)."""
    resp = client.post("/devices", json=NEW_DEVICE, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return body["device"]["device_uid"], body["enrollment_secret"]


def _device_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_enroll_success(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, secret = _create_device(client, headers)

    resp = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["device_token"]
    assert body["device"]["enrollment_status"] == "enrolled"


def test_enroll_wrong_secret(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, _ = _create_device(client, headers)
    resp = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": "wrong"}
    )
    assert resp.status_code == 401


def test_enroll_unknown_device(client):
    resp = client.post(
        "/agent/enroll",
        json={"device_uid": "dev_does_not_exist", "enrollment_secret": "x"},
    )
    assert resp.status_code == 401


def test_enroll_is_single_use(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, secret = _create_device(client, headers)
    first = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    )
    assert first.status_code == 200
    # Re-enrolling with the same secret must fail (device no longer pending).
    second = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    )
    assert second.status_code == 401


def test_heartbeat_requires_device_token(client):
    assert client.post("/agent/heartbeat", json={}).status_code == 401


def test_heartbeat_updates_last_seen_and_version(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, secret = _create_device(client, headers)
    token = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    ).json()["device_token"]

    resp = client.post(
        "/agent/heartbeat",
        json={"agent_version": "1.2.3", "os_version": "Windows 11 26H2"},
        headers=_device_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["enrollment_status"] == "enrolled"

    # The admin view reflects the reported data and a recent check-in.
    device = client.get(f"/devices/{uid}", headers=headers).json()
    assert device["agent_version"] == "1.2.3"
    assert device["os_version"] == "Windows 11 26H2"
    assert device["last_seen_at"] is not None


def test_admin_token_rejected_on_heartbeat(client, auth_headers, make_admin):
    # A valid admin access token must not authenticate a device endpoint.
    admin_id, _, _ = make_admin(email="x@example.com")
    access = create_access_token(admin_id)
    resp = client.post(
        "/agent/heartbeat", json={}, headers=_device_headers(access)
    )
    assert resp.status_code == 401


def test_device_token_rejected_on_admin_endpoint(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, secret = _create_device(client, headers)
    token = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    ).json()["device_token"]
    # A device token must not grant access to admin endpoints.
    resp = client.get("/devices", headers=_device_headers(token))
    assert resp.status_code == 401


def test_revoked_device_cannot_heartbeat(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, secret = _create_device(client, headers)
    token = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    ).json()["device_token"]
    assert client.post(f"/devices/{uid}/revoke", headers=headers).status_code == 200
    # The previously valid device token is now rejected.
    resp = client.post("/agent/heartbeat", json={}, headers=_device_headers(token))
    assert resp.status_code == 401


def test_enroll_rate_limited(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, _ = _create_device(client, headers)
    for _ in range(settings.login_max_attempts):
        r = client.post(
            "/agent/enroll", json={"device_uid": uid, "enrollment_secret": "bad"}
        )
        assert r.status_code == 401
    blocked = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": "bad"}
    )
    assert blocked.status_code == 429
