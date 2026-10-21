"""Tests for device location: policy, request, reporting, freshness, access."""

from __future__ import annotations

from app.models.enums import Role

NEW_DEVICE = {"name": "Loc Laptop", "os_type": "windows", "device_type": "laptop"}


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


def test_location_defaults_none(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    uid, _ = _enroll(client, headers)
    resp = client.get(f"/devices/{uid}/location", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False
    assert body["freshness"] == "none"
    assert body["latest"] is None


def test_location_view_requires_auth(client):
    assert client.get("/devices/dev_x/location").status_code == 401


def test_update_location_policy_requires_manage_security(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, _ = _enroll(client, owner)
    admin = auth_headers(email="a2@example.com", role=Role.ADMIN)
    body = {"enabled": True, "retention_days": 7}
    assert (
        client.put(f"/devices/{uid}/location-policy", json=body, headers=admin).status_code
        == 403
    )
    ok = client.put(f"/devices/{uid}/location-policy", json=body, headers=owner)
    assert ok.status_code == 200
    assert ok.json()["enabled"] is True


def test_report_requires_device_token(client):
    assert client.post("/agent/location", json={"status": "unavailable"}).status_code == 401


def test_request_then_report_fix(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, token = _enroll(client, owner)

    assert client.post(f"/devices/{uid}/location/request", headers=owner).status_code == 202
    directives = client.get("/agent/directives", headers=_dev(token)).json()
    assert directives["location_requested"] is True

    resp = client.post(
        "/agent/location",
        json={"status": "ok", "latitude": -1.2921, "longitude": 36.8219, "accuracy_m": 25},
        headers=_dev(token),
    )
    assert resp.status_code == 204

    # Request is cleared, and the fix shows as current with its source.
    directives = client.get("/agent/directives", headers=_dev(token)).json()
    assert directives["location_requested"] is False
    loc = client.get(f"/devices/{uid}/location", headers=owner).json()
    assert loc["freshness"] == "current"
    assert loc["latest"]["latitude"] == -1.2921
    assert loc["latest"]["source"] == "windows_agent"


def test_unavailable_not_stored_as_coordinates(client, auth_headers):
    owner = auth_headers(role=Role.OWNER)
    uid, token = _enroll(client, owner)
    resp = client.post(
        "/agent/location", json={"status": "unavailable"}, headers=_dev(token)
    )
    assert resp.status_code == 204
    loc = client.get(f"/devices/{uid}/location", headers=owner).json()
    assert loc["latest"] is None
    assert loc["freshness"] == "none"
