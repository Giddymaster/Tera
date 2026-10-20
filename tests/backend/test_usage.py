"""Tests for device health on heartbeat and app-usage reporting/viewing."""

from __future__ import annotations

from app.models.enums import Role

NEW_DEVICE = {"name": "Usage Laptop", "os_type": "windows", "device_type": "laptop"}


def _enroll(client, headers) -> tuple[str, str]:
    """Create + enroll a device; return (device_uid, device_token)."""
    created = client.post("/devices", json=NEW_DEVICE, headers=headers).json()
    uid = created["device"]["device_uid"]
    secret = created["enrollment_secret"]
    token = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    ).json()["device_token"]
    return uid, token


def _dev(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_heartbeat_stores_health(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, token = _enroll(client, headers)
    resp = client.post(
        "/agent/heartbeat",
        json={
            "disk_free_gb": 123.4,
            "disk_total_gb": 500.0,
            "battery_percent": 88,
            "power_plugged": True,
        },
        headers=_dev(token),
    )
    assert resp.status_code == 200
    device = client.get(f"/devices/{uid}", headers=headers).json()
    assert device["disk_free_gb"] == 123.4
    assert device["battery_percent"] == 88
    assert device["power_plugged"] is True


def test_heartbeat_rejects_bad_battery(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    _, token = _enroll(client, headers)
    resp = client.post(
        "/agent/heartbeat", json={"battery_percent": 150}, headers=_dev(token)
    )
    assert resp.status_code == 422


def test_usage_requires_device_token(client):
    resp = client.post(
        "/agent/usage", json={"entries": [{"app_name": "chrome.exe", "seconds": 60}]}
    )
    assert resp.status_code == 401


def test_usage_submit_and_aggregate(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, token = _enroll(client, headers)

    # Two reports for the same app should accumulate.
    client.post(
        "/agent/usage",
        json={"entries": [{"app_name": "Code.exe", "seconds": 100}]},
        headers=_dev(token),
    )
    client.post(
        "/agent/usage",
        json={
            "entries": [
                {"app_name": "Code.exe", "seconds": 50},
                {"app_name": "chrome.exe", "seconds": 30},
            ]
        },
        headers=_dev(token),
    )

    summary = client.get(f"/devices/{uid}/usage", headers=headers).json()
    assert summary["total_seconds"] == 180
    by_app = {a["app_name"]: a["seconds"] for a in summary["apps"]}
    assert by_app["Code.exe"] == 150
    assert by_app["chrome.exe"] == 30
    # Ordered by seconds descending.
    assert summary["apps"][0]["app_name"] == "Code.exe"


def test_usage_view_requires_auth(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, _ = _enroll(client, headers)
    assert client.get(f"/devices/{uid}/usage").status_code == 401


def test_usage_validation_rejects_empty(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    _, token = _enroll(client, headers)
    resp = client.post("/agent/usage", json={"entries": []}, headers=_dev(token))
    assert resp.status_code == 422
