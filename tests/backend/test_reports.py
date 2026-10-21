"""Tests for derived alerts and the fleet summary report."""

from __future__ import annotations

from app.models.enums import Role

WIN = {"name": "R1", "os_type": "windows", "device_type": "laptop"}


def _enroll(client, headers, device=WIN) -> tuple[str, str]:
    created = client.post("/devices", json=device, headers=headers).json()
    uid = created["device"]["device_uid"]
    secret = created["enrollment_secret"]
    token = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    ).json()["device_token"]
    return uid, token


def test_alerts_requires_auth(client):
    assert client.get("/alerts").status_code == 401


def test_pending_device_raises_alert(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    # Created but never enrolled -> pending.
    client.post("/devices", json=WIN, headers=headers)
    alerts = client.get("/alerts", headers=headers).json()
    assert any(a["type"] == "pending" for a in alerts)


def test_low_disk_and_update_alerts(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    _, token = _enroll(client, headers)
    client.post(
        "/agent/heartbeat",
        json={"agent_version": "0.0.1", "disk_free_gb": 1.0, "disk_total_gb": 500.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    types = {a["type"] for a in client.get("/alerts", headers=headers).json()}
    assert "low_disk" in types
    assert "update" in types


def test_alerts_sorted_warnings_first(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    _, token = _enroll(client, headers)
    client.post(
        "/agent/heartbeat",
        json={"agent_version": "0.0.1", "disk_free_gb": 1.0, "disk_total_gb": 500.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    sev = [a["severity"] for a in client.get("/alerts", headers=headers).json()]
    # No "info" should appear before a "warning".
    assert sev == sorted(sev, key=lambda s: 0 if s == "warning" else 1)


def test_summary_requires_view_reports(client):
    assert client.get("/reports/summary").status_code == 401


def test_summary_counts(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    client.post("/devices", json=WIN, headers=headers)  # pending
    _enroll(client, headers, {"name": "P", "os_type": "android", "device_type": "phone"})

    summary = client.get("/reports/summary", headers=headers).json()
    assert summary["total_devices"] >= 2
    assert summary["pending"] >= 1
    assert "windows" in summary["by_os"]
    assert "android" in summary["by_os"]
