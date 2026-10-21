"""Tests for the Apple MDM status endpoint (not-configured path)."""

from __future__ import annotations

from app.models.enums import Role


def test_apple_status_not_configured(client, auth_headers):
    headers = auth_headers(role=Role.OWNER)
    resp = client.get("/apple/status", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is False
    # Honest capability matrix.
    assert body["capabilities"]["remote_wipe"] is True
    assert body["capabilities"]["screenshots"] is False
    assert body["capabilities"]["lost_mode"] == "supervised_only"
    assert body["capabilities"]["location"] == "lost_mode_supervised_only"
    assert len(body["enrollment_models"]) >= 1


def test_apple_status_requires_auth(client):
    assert client.get("/apple/status").status_code == 401
