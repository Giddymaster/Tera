"""Foreground application usage, aggregated per device, per app, per day.

Stores only the application name and a duration. It never stores window titles,
document names, URLs, page contents, or keystrokes.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AppUsage(Base):
    __tablename__ = "app_usage"
    __table_args__ = (
        UniqueConstraint("device_id", "app_name", "day", name="uq_usage_device_app_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    app_name: Mapped[str] = mapped_column(String(120), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    seconds: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
