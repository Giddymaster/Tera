"""Tests for authorized live remote-support sessions."""

from __future__ import annotations

import base64

from app.models.enums import Role

NEW_DEVICE = {"name": "Session Laptop", "os_type": "windows", "device_type": "laptop"}
FAKE_B64 = base64.b64encode(b"SESSION-FRAME-BYTES").decode()


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


def test_start_session_requires_permission(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, _ = _enroll(client, owner)
    viewer = auth_headers(email="viewer@example.com", role=Role.VIEWER)
    assert client.post(f"/devices/{uid}/sessions", headers=viewer).status_code == 403


def test_start_session_records_initiator(client, auth_headers):
    admin = auth_headers(email="support@example.com", role=Role.ADMIN)
    # Need an owner to create the device first.
    owner = auth_headers(role=Role.OWNER)
    uid, _ = _enroll(client, owner)
    resp = client.post(f"/devices/{uid}/sessions", headers=admin)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "active"
    assert body["initiated_by_email"] == "support@example.com"


def test_directives_report_active_session(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, token = _enroll(client, owner)
    session_id = client.post(f"/devices/{uid}/sessions", headers=owner).json()["id"]

    directives = client.get("/agent/directives", headers=_dev(token)).json()
    assert directives["session_active"] is True
    assert directives["session_id"] == session_id


def test_session_snapshot_flow_and_end(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, token = _enroll(client, owner)
    session_id = client.post(f"/devices/{uid}/sessions", headers=owner).json()["id"]

    # Agent uploads a session snapshot.
    up = client.post(
        "/agent/screenshot",
        json={"image_base64": FAKE_B64, "trigger": "session", "session_id": session_id},
        headers=_dev(token),
    )
    assert up.status_code == 201

    frames = client.get(f"/sessions/{session_id}/screenshots", headers=owner).json()
    assert len(frames) == 1

    # End the session.
    ended = client.post(f"/sessions/{session_id}/end", headers=owner).json()
    assert ended["status"] == "ended"
    assert ended["ended_at"] is not None

    # Device no longer sees it as active.
    directives = client.get("/agent/directives", headers=_dev(token)).json()
    assert directives["session_active"] is False


def test_starting_twice_reuses_active_session(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, _ = _enroll(client, owner)
    first = client.post(f"/devices/{uid}/sessions", headers=owner).json()["id"]
    second = client.post(f"/devices/{uid}/sessions", headers=owner).json()["id"]
    assert first == second
