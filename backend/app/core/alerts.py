"""Derive device alerts from current device state (no separate alerts table)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import get_settings
from app.models.device import Device
from app.models.enums import EnrollmentStatus

OFFLINE_SECONDS = 15 * 60
LOW_DISK_FRACTION = 0.10
LOW_BATTERY_PERCENT = 15


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def compute_device_alerts(device: Device, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    settings = get_settings()
    base = {
        "device_uid": device.device_uid,
        "device_name": device.name,
        "os_type": device.os_type.value,
    }
    alerts: list[dict] = []

    if device.enrollment_status == EnrollmentStatus.ENROLLED:
        last = _aware(device.last_seen_at)
        if last is None or (now - last).total_seconds() > OFFLINE_SECONDS:
            alerts.append(
                {**base, "severity": "warning", "type": "offline",
                 "message": "Device offline (no recent check-in)"}
            )
    elif device.enrollment_status == EnrollmentStatus.PENDING:
        alerts.append(
            {**base, "severity": "info", "type": "pending",
             "message": "Awaiting first check-in"}
        )

    if (
        device.disk_total_gb
        and device.disk_free_gb is not None
        and device.disk_total_gb > 0
        and device.disk_free_gb / device.disk_total_gb < LOW_DISK_FRACTION
    ):
        alerts.append(
            {**base, "severity": "warning", "type": "low_disk",
             "message": f"Low disk: {device.disk_free_gb:.0f} GB free"}
        )

    if (
        device.battery_percent is not None
        and device.battery_percent < LOW_BATTERY_PERCENT
        and device.power_plugged is False
    ):
        alerts.append(
            {**base, "severity": "info", "type": "low_battery",
             "message": f"Low battery: {device.battery_percent}%"}
        )

    if device.agent_version and device.agent_version != settings.agent_latest_version:
        alerts.append(
            {**base, "severity": "info", "type": "update",
             "message": "Agent update available"}
        )

    return alerts


# Sort key: warnings before info.
def severity_rank(severity: str) -> int:
    return {"warning": 0, "info": 1}.get(severity, 2)
