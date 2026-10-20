"""Tests for agent version reporting and update awareness."""

from __future__ import annotations

from app.core.config import get_settings
from app.models.enums import Role

settings = get_settings()

NEW_DEVICE = {"name": "Versioned Laptop", "os_type": "windows", "device_type": "laptop"}


def _enroll(client, headers) -> str:
    created = client.post("/devices", json=NEW_DEVICE, headers=headers).json()
    uid = created["device"]["device_uid"]
    secret = created["enrollment_secret"]
    return client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    ).json()["device_token"]


def test_meta_reports_latest_agent_version(client):
    resp = client.get("/meta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["latest_agent_version"] == settings.agent_latest_version
    assert "server_version" in body


def test_heartbeat_flags_outdated_agent(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    token = _enroll(client, headers)
    resp = client.post(
        "/agent/heartbeat",
        json={"agent_version": "0.0.1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["latest_agent_version"] == settings.agent_latest_version
    assert body["update_available"] is True


def test_heartbeat_current_agent_no_update(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    token = _enroll(client, headers)
    resp = client.post(
        "/agent/heartbeat",
        json={"agent_version": settings.agent_latest_version},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["update_available"] is False
