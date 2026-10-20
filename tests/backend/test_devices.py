"""Tests for device management endpoints and their authorization."""

from __future__ import annotations

from app.models.enums import Role

NEW_DEVICE = {"name": "Office Laptop 1", "os_type": "windows", "device_type": "laptop"}


def test_create_device_requires_auth(client):
    assert client.post("/devices", json=NEW_DEVICE).status_code == 401


def test_viewer_cannot_create_device(client, auth_headers):
    headers = auth_headers(email="viewer@example.com", role=Role.VIEWER)
    resp = client.post("/devices", json=NEW_DEVICE, headers=headers)
    assert resp.status_code == 403


def test_owner_can_create_device_and_get_secret_once(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    resp = client.post("/devices", json=NEW_DEVICE, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["enrollment_secret"]  # shown exactly once
    device = body["device"]
    assert device["device_uid"].startswith("dev_")
    assert device["enrollment_status"] == "pending"
    # The secret (or its hash) must never appear in the device representation.
    assert "enrollment_secret" not in device
    assert "enrollment_secret_hash" not in device

    # Fetching the device later does not expose any secret.
    got = client.get(f"/devices/{device['device_uid']}", headers=headers)
    assert got.status_code == 200
    assert "enrollment_secret" not in got.json()


def test_viewer_can_list_devices(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    client.post("/devices", json=NEW_DEVICE, headers=owner)
    viewer = auth_headers(email="viewer@example.com", role=Role.VIEWER)
    resp = client.get("/devices", headers=viewer)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_missing_device_404(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    assert client.get("/devices/dev_missing", headers=headers).status_code == 404


def test_revoke_device(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid = client.post("/devices", json=NEW_DEVICE, headers=headers).json()["device"][
        "device_uid"
    ]
    resp = client.post(f"/devices/{uid}/revoke", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["enrollment_status"] == "revoked"


def test_delete_device(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid = client.post("/devices", json=NEW_DEVICE, headers=headers).json()["device"][
        "device_uid"
    ]
    assert client.delete(f"/devices/{uid}", headers=headers).status_code == 204
    assert client.get(f"/devices/{uid}", headers=headers).status_code == 404


def test_viewer_cannot_delete(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid = client.post("/devices", json=NEW_DEVICE, headers=owner).json()["device"][
        "device_uid"
    ]
    viewer = auth_headers(email="viewer@example.com", role=Role.VIEWER)
    assert client.delete(f"/devices/{uid}", headers=viewer).status_code == 403


def test_create_device_invalid_os_type(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    bad = {"name": "X", "os_type": "blackberry", "device_type": "laptop"}
    assert client.post("/devices", json=bad, headers=headers).status_code == 422


def test_create_device_missing_name(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    bad = {"os_type": "windows", "device_type": "laptop"}
    assert client.post("/devices", json=bad, headers=headers).status_code == 422
