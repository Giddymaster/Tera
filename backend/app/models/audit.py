"""Audit log model: an append-only record of administrator actions."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

    # Who acted. We keep the admin id (nullable, for system events or deleted
    # admins) and a snapshot of the email so the log stays meaningful even if
    # the admin record is later removed.
    actor_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    action: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<AuditLog {self.action} actor={self.actor_email!r} at {self.timestamp}>"
