"""Location retention cleanup."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monitoring import LocationPoint

# A stored fix newer than this is "current"; older is "stale".
CURRENT_THRESHOLD_SECONDS = 15 * 60


async def delete_expired(session: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    ids = (
        await session.execute(
            select(LocationPoint.id).where(LocationPoint.retention_until < now)
        )
    ).scalars().all()
    if ids:
        await session.execute(delete(LocationPoint).where(LocationPoint.id.in_(ids)))
        await session.commit()
    return len(ids)
