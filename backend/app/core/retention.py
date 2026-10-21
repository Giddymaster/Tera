"""Consolidated data-retention cleanup across all stored data types.

Screenshots and location points also have per-device retention applied
opportunistically; this module adds retention for the aggregate usage and audit
stores and provides a single entry point that runs every cleanup.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.location import delete_expired as delete_expired_locations
from app.core.screenshots import delete_expired as delete_expired_screenshots
from app.models.audit import AuditLog
from app.models.usage import AppUsage


async def delete_old_usage(session: AsyncSession) -> int:
    cutoff = datetime.now(timezone.utc).date() - timedelta(
        days=get_settings().usage_retention_days
    )
    ids = (
        await session.execute(select(AppUsage.id).where(AppUsage.day < cutoff))
    ).scalars().all()
    if ids:
        await session.execute(delete(AppUsage).where(AppUsage.id.in_(ids)))
        await session.commit()
    return len(ids)


async def delete_old_audit(session: AsyncSession) -> int:
    # Stored audit timestamps are naive UTC (SQLite), so compare naive-to-naive.
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        days=get_settings().audit_retention_days
    )
    ids = (
        await session.execute(select(AuditLog.id).where(AuditLog.timestamp < cutoff))
    ).scalars().all()
    if ids:
        await session.execute(delete(AuditLog).where(AuditLog.id.in_(ids)))
        await session.commit()
    return len(ids)


async def run_all(session: AsyncSession) -> dict[str, int]:
    return {
        "screenshots": await delete_expired_screenshots(session),
        "locations": await delete_expired_locations(session),
        "usage": await delete_old_usage(session),
        "audit": await delete_old_audit(session),
    }
