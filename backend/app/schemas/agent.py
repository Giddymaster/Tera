"""Device agent request/response schemas (enrollment and heartbeat)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.device import DeviceOut


class EnrollRequest(BaseModel):
    device_uid: str = Field(min_length=1, max_length=64)
    enrollment_secret: str = Field(min_length=1, max_length=256)


class EnrollResponse(BaseModel):
    """Returned once on successful enrollment.

    ``device_token`` authenticates all later agent calls. Store it securely on
    the device; it is not retrievable again.
    """

    device_token: str
    device: DeviceOut


class HeartbeatRequest(BaseModel):
    # Optional health info the agent reports.
    agent_version: str | None = Field(default=None, max_length=40)
    os_version: str | None = Field(default=None, max_length=80)
    disk_free_gb: float | None = Field(default=None, ge=0)
    disk_total_gb: float | None = Field(default=None, ge=0)
    battery_percent: int | None = Field(default=None, ge=0, le=100)
    power_plugged: bool | None = None


class HeartbeatResponse(BaseModel):
    ok: bool = True
    enrollment_status: str
    last_seen_at: datetime
    server_time: datetime
    latest_agent_version: str
    update_available: bool = False


class RustDeskReportIn(BaseModel):
    rustdesk_id: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)
