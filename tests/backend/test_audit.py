"""Tests that administrator actions are recorded in the audit log."""

from __future__ import annotations

from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.enums import Role


def _actions(session) -> list[str]:
    return list(session.execute(select(AuditLog.action)).scalars().all())


def test_successful_login_is_audited(client, make_admin, sync_session):
    _, email, password = make_admin()
    client.post("/auth/login", json={"email": email, "password": password})
    assert "admin.login" in _actions(sync_session)


def test_failed_login_is_audited(client, make_admin, sync_session):
    _, email, _ = make_admin()
    client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert "admin.login_failed" in _actions(sync_session)


def test_device_create_is_audited(client, auth_headers, sync_session):
    headers = auth_headers(role=Role.OWNER)
    client.post(
        "/devices",
        json={"name": "L1", "os_type": "windows", "device_type": "laptop"},
        headers=headers,
    )
    actions = _actions(sync_session)
    assert "device.create" in actions


def test_audit_entry_has_no_password(client, make_admin, sync_session):
    _, email, password = make_admin()
    client.post("/auth/login", json={"email": email, "password": password})
    rows = sync_session.execute(select(AuditLog)).scalars().all()
    for row in rows:
        blob = f"{row.detail or ''}".lower()
        assert password.lower() not in blob
