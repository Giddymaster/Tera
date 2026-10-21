"""Schemas for alerts and the fleet summary report."""

from __future__ import annotations

from pydantic import BaseModel


class AlertOut(BaseModel):
    device_uid: str
    device_name: str
    os_type: str
    severity: str
    type: str
    message: str


class ReportSummaryOut(BaseModel):
    total_devices: int
    online: int
    offline: int
    pending: int
    revoked: int
    by_os: dict[str, int]
    alerts_total: int
    alerts_warning: int
    active_sessions: int
    screenshots_total: int
    updates_available: int
