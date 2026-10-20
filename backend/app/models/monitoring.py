"""Models for screenshots, capture policy/requests, and remote-support sessions.

Design notes:
- Screenshot image bytes are stored encrypted on disk (see core/encryption.py);
  the DB holds only metadata and the storage path.
- A screenshot is only ever created by an authenticated, enrolled device, and is
  only viewable by admins holding the screenshots permission.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ScreenshotPolicy(Base):
    """Per-device screenshot capture policy. Disabled by default."""

    __tablename__ = "screenshot_policy"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), unique=True, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    # Optional active window (local device hours, 0-23). Null = any time.
    active_hour_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active_hour_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retention_days: Mapped[int] = mapped_column(Integer, default=30)
    # Comma-separated app names to skip (best-effort privacy, e.g. password apps).
    excluded_apps: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class CaptureRequest(Base):
    """A one-off, admin-initiated request for the device to capture now."""

    __tablename__ = "capture_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    requested_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    fulfilled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RemoteSession(Base):
    """An authorized live remote-support session."""

    __tablename__ = "remote_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    initiated_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    initiated_by_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_reason: Mapped[str | None] = mapped_column(String(40), nullable=True)


class Screenshot(Base):
    __tablename__ = "screenshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    # 'schedule' | 'request' | 'session'
    trigger: Mapped[str] = mapped_column(String(16), default="schedule")
    requested_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("remote_sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    foreground_app: Mapped[str | None] = mapped_column(String(120), nullable=True)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    # Path to the encrypted blob on disk (relative to the screenshots dir).
    storage_path: Mapped[str] = mapped_column(String(255))
    retention_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )
