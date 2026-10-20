"""Helper for writing audit-log entries."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.models.audit import AuditLog


async def record_action(
    session: AsyncSession,
    *,
    action: str,
    actor: Admin | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    commit: bool = True,
) -> AuditLog:
    """Append an audit entry. Does not store any secret or password."""
    entry = AuditLog(
        actor_admin_id=actor.id if actor else None,
        actor_email=actor.email if actor else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=ip_address,
    )
    session.add(entry)
    if commit:
        await session.commit()
    return entry
