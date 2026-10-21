"""Tests for encrypted backup/restore and usage/audit retention cleanup."""

from __future__ import annotations

import asyncio
from datetime import date, datetime

from sqlalchemy import func, select

from app.core.backup import SQLITE_MAGIC, create_backup, restore_backup
from app.core.database import SessionLocal
from app.core.retention import delete_old_audit, delete_old_usage
from app.models.audit import AuditLog
from app.models.enums import Role
from app.models.usage import AppUsage


def test_backup_restore_roundtrip(client, auth_headers, tmp_path):
    # Make sure there is some data to back up.
    auth_headers(role=Role.OWNER)
    backup = create_backup(tmp_path / "bk")
    assert backup.exists()
    assert backup.suffix == ".enc"

    restored = restore_backup(backup, tmp_path / "restored.db")
    # The decrypted file is a real SQLite database.
    assert restored.read_bytes().startswith(SQLITE_MAGIC)


def test_usage_and_audit_retention(client, auth_headers, sync_session):
    # Insert rows far older than the retention window.
    sync_session.add(
        AppUsage(device_id=1, app_name="old.exe", day=date(2000, 1, 1), seconds=5)
    )
    sync_session.add(AuditLog(action="old.event", timestamp=datetime(2000, 1, 1)))
    sync_session.commit()

    async def _run() -> tuple[int, int]:
        async with SessionLocal() as s:
            return await delete_old_usage(s), await delete_old_audit(s)

    removed_usage, removed_audit = asyncio.run(_run())
    assert removed_usage >= 1
    assert removed_audit >= 1

    sync_session.rollback()
    old_usage = sync_session.scalar(
        select(func.count()).select_from(AppUsage).where(AppUsage.day < date(2001, 1, 1))
    )
    assert old_usage == 0
