"""Tests for the admin audit-log endpoint."""

from __future__ import annotations

from app.models.enums import Role

NEW_DEVICE = {"name": "Audited Laptop", "os_type": "windows", "device_type": "laptop"}


def test_audit_requires_auth(client):
    assert client.get("/audit").status_code == 401


def test_audit_lists_actions(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    # Generate an auditable action.
    client.post("/devices", json=NEW_DEVICE, headers=headers)

    resp = client.get("/audit", headers=headers)
    assert resp.status_code == 200
    actions = [row["action"] for row in resp.json()]
    assert "device.create" in actions
    assert "admin.login" in actions


def test_audit_newest_first(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    client.post("/devices", json=NEW_DEVICE, headers=headers)
    rows = client.get("/audit", headers=headers).json()
    timestamps = [r["timestamp"] for r in rows]
    assert timestamps == sorted(timestamps, reverse=True)


def test_audit_limit(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    for i in range(3):
        client.post(
            "/devices",
            json={**NEW_DEVICE, "name": f"L{i}"},
            headers=headers,
        )
    rows = client.get("/audit?limit=2", headers=headers).json()
    assert len(rows) == 2
