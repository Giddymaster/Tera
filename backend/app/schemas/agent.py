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
    # Optional health info the agent reports. More fields arrive in Milestone 5.
    agent_version: str | None = Field(default=None, max_length=40)
    os_version: str | None = Field(default=None, max_length=80)


class HeartbeatResponse(BaseModel):
    ok: bool = True
    enrollment_status: str
    last_seen_at: datetime
    server_time: datetime
