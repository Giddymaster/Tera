"""Company-owned device model."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import DeviceType, EnrollmentStatus, OSType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Public, opaque identifier used by the agent and the dashboard URL.
    device_uid: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    name: Mapped[str] = mapped_column(String(120))
    os_type: Mapped[OSType] = mapped_column(SAEnum(OSType, native_enum=False, length=16))
    device_type: Mapped[DeviceType] = mapped_column(
        SAEnum(DeviceType, native_enum=False, length=16)
    )
    assigned_to: Mapped[str | None] = mapped_column(String(120), nullable=True)

    enrollment_status: Mapped[EnrollmentStatus] = mapped_column(
        SAEnum(EnrollmentStatus, native_enum=False, length=16),
        default=EnrollmentStatus.PENDING,
    )
    # Argon2 hash of the one-time enrollment secret. The plaintext secret is
    # shown to the admin exactly once at creation and never stored.
    enrollment_secret_hash: Mapped[str] = mapped_column(String(255))

    enrolled_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )

    # Reported by the agent on check-in (Milestone 4+). Null until first report.
    agent_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    os_version: Mapped[str | None] = mapped_column(String(80), nullable=True)

    # Latest health snapshot reported by the agent (Milestone 5).
    disk_free_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    disk_total_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_plugged: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # RustDesk remote control: the device's RustDesk ID and its unattended
    # password (encrypted at rest; only revealed to authorized admins).
    rustdesk_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rustdesk_password_enc: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    # Set on each successful agent check-in (heartbeat arrives in Milestone 4).
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<Device uid={self.device_uid!r} os={self.os_type} "
            f"status={self.enrollment_status}>"
        )
