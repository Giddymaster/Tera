"""Tests for the Android management endpoints (not-configured path).

The live AMAPI path needs real Google credentials and a device, so these tests
cover status reporting, authorization, and the clear "not configured" behavior.
"""

from __future__ import annotations

from app.models.enums import Role


def test_status_reports_not_configured(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    resp = client.get("/android/status", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is False
    # Capability matrix is always advertised, with honest limits.
    assert body["capabilities"]["remote_wipe"] is True
    assert body["capabilities"]["screenshots"] is False
    assert body["capabilities"]["location"] == "lost_mode_only"
    assert "WIPE" in body["commands"]


def test_status_requires_auth(client):
    assert client.get("/android/status").status_code == 401


def test_devices_not_configured_returns_503(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    resp = client.get("/android/devices", headers=headers)
    assert resp.status_code == 503
    assert "not configured" in resp.json()["detail"].lower()


def test_enrollment_token_requires_manage_devices(client, auth_headers):
    viewer = auth_headers(email="viewer@example.com", role=Role.VIEWER)
    assert client.post("/android/enrollment-token", headers=viewer).status_code == 403


def test_enrollment_token_not_configured_returns_503(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    resp = client.post("/android/enrollment-token", headers=headers)
    assert resp.status_code == 503


def test_command_rejects_unknown_type(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    resp = client.post(
        "/android/command",
        json={"device_name": "enterprises/x/devices/y", "type": "FORMAT_C"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_command_not_configured_returns_503(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    resp = client.post(
        "/android/command",
        json={"device_name": "enterprises/x/devices/y", "type": "LOCK"},
        headers=headers,
    )
    assert resp.status_code == 503
