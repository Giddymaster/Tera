"""Security headers and full device-data deletion (cascade + blob cleanup)."""

from __future__ import annotations

import base64
from pathlib import Path

from sqlalchemy import func, select

from app.core.config import get_settings
from app.models.device import Device
from app.models.enums import Role
from app.models.monitoring import LocationPoint, Screenshot
from app.models.usage import AppUsage

FAKE_B64 = base64.b64encode(b"SHOT").decode()
DEVICE = {"name": "Del Laptop", "os_type": "windows", "device_type": "laptop"}


def test_security_headers_present(client):
    resp = client.get("/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in resp.headers["content-security-policy"]
    # HSTS is only asserted in production.
    assert "strict-transport-security" not in resp.headers


def test_delete_device_removes_all_data_and_blobs(client, auth_headers, sync_session):
    owner = auth_headers(role=Role.OWNER)
    created = client.post("/devices", json=DEVICE, headers=owner).json()
    uid = created["device"]["device_uid"]
    secret = created["enrollment_secret"]
    token = client.post(
        "/agent/enroll", json={"device_uid": uid, "enrollment_secret": secret}
    ).json()["device_token"]
    dev_auth = {"Authorization": f"Bearer {token}"}

    # Generate associated data across stores.
    client.post(
        "/agent/screenshot",
        json={"image_base64": FAKE_B64, "trigger": "schedule"},
        headers=dev_auth,
    )
    client.post(
        "/agent/usage",
        json={"entries": [{"app_name": "x.exe", "seconds": 10}]},
        headers=dev_auth,
    )
    client.post(
        "/agent/location",
        json={"status": "ok", "latitude": 1.0, "longitude": 2.0},
        headers=dev_auth,
    )

    # Find the device id and the screenshot blob path on disk.
    device_id = sync_session.scalar(select(Device.id).where(Device.device_uid == uid))
    storage_path = sync_session.scalar(
        select(Screenshot.storage_path).where(Screenshot.device_id == device_id)
    )
    blob = Path(get_settings().screenshot_dir) / storage_path
    assert blob.exists()

    # Delete the device.
    assert client.delete(f"/devices/{uid}", headers=owner).status_code == 204

    # End the read transaction so the next queries see the committed delete.
    sync_session.rollback()
    assert sync_session.scalar(select(Device.id).where(Device.device_uid == uid)) is None
    for model in (Screenshot, AppUsage, LocationPoint):
        count = sync_session.scalar(
            select(func.count()).select_from(model).where(model.device_id == device_id)
        )
        assert count == 0, model.__name__
    assert not blob.exists()
