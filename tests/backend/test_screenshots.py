"""Tests for screenshot policy, capture requests, upload, viewing, and access."""

from __future__ import annotations

import base64

from app.models.enums import Role

NEW_DEVICE = {"name": "Shot Laptop", "os_type": "windows", "device_type": "laptop"}
FAKE_IMAGE = b"FAKE-JPEG-BYTES-0123456789"
FAKE_B64 = base64.b64encode(FAKE_IMAGE).decode()


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


def test_policy_defaults_disabled(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, _ = _enroll(client, headers)
    resp = client.get(f"/devices/{uid}/screenshot-policy", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


def test_update_policy_requires_manage_security(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, _ = _enroll(client, owner)
    body = {"enabled": True, "interval_minutes": 10, "retention_days": 7}

    # An ADMIN lacks manage_security_policy.
    admin = auth_headers(email="admin2@example.com", role=Role.ADMIN)
    assert (
        client.put(f"/devices/{uid}/screenshot-policy", json=body, headers=admin).status_code
        == 403
    )
    # OWNER may change it.
    ok = client.put(f"/devices/{uid}/screenshot-policy", json=body, headers=owner)
    assert ok.status_code == 200
    assert ok.json()["enabled"] is True
    assert ok.json()["interval_minutes"] == 10


def test_capture_request_upload_and_view(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, token = _enroll(client, owner)

    assert (
        client.post(f"/devices/{uid}/screenshots/request", headers=owner).status_code
        == 202
    )
    directives = client.get("/agent/directives", headers=_dev(token)).json()
    assert directives["capture_requested"] is True

    up = client.post(
        "/agent/screenshot",
        json={"image_base64": FAKE_B64, "trigger": "request", "foreground_app": "x.exe"},
        headers=_dev(token),
    )
    assert up.status_code == 201

    # The pending request is now fulfilled.
    directives = client.get("/agent/directives", headers=_dev(token)).json()
    assert directives["capture_requested"] is False

    shots = client.get(f"/devices/{uid}/screenshots", headers=owner).json()
    assert len(shots) == 1
    assert shots[0]["trigger"] == "request"

    # The decrypted image round-trips exactly.
    img = client.get(f"/screenshots/{shots[0]['id']}/image", headers=owner)
    assert img.status_code == 200
    assert img.headers["content-type"] == "image/jpeg"
    assert img.content == FAKE_IMAGE


def test_screenshot_access_requires_permission(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, token = _enroll(client, owner)
    client.post(
        "/agent/screenshot",
        json={"image_base64": FAKE_B64, "trigger": "schedule"},
        headers=_dev(token),
    )
    shots = client.get(f"/devices/{uid}/screenshots", headers=owner).json()
    sid = shots[0]["id"]

    # A VIEWER lacks view_screenshots.
    viewer = auth_headers(email="viewer@example.com", role=Role.VIEWER)
    assert client.get(f"/devices/{uid}/screenshots", headers=viewer).status_code == 403
    assert client.get(f"/screenshots/{sid}/image", headers=viewer).status_code == 403


def test_upload_requires_device_token(client):
    resp = client.post(
        "/agent/screenshot", json={"image_base64": FAKE_B64, "trigger": "schedule"}
    )
    assert resp.status_code == 401


def test_delete_screenshot(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, token = _enroll(client, owner)
    client.post(
        "/agent/screenshot",
        json={"image_base64": FAKE_B64, "trigger": "schedule"},
        headers=_dev(token),
    )
    sid = client.get(f"/devices/{uid}/screenshots", headers=owner).json()[0]["id"]
    assert client.delete(f"/screenshots/{sid}", headers=owner).status_code == 204
    assert client.get(f"/screenshots/{sid}/image", headers=owner).status_code == 404


def test_upload_rejects_empty_image(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    _, token = _enroll(client, owner)
    resp = client.post(
        "/agent/screenshot",
        json={"image_base64": base64.b64encode(b"").decode(), "trigger": "schedule"},
        headers=_dev(token),
    )
    assert resp.status_code in (400, 422)
