"""Device request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DeviceType, EnrollmentStatus, OSType


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    os_type: OSType
    device_type: DeviceType
    assigned_to: str | None = Field(default=None, max_length=120)


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_uid: str
    name: str
    os_type: OSType
    device_type: DeviceType
    assigned_to: str | None
    enrollment_status: EnrollmentStatus
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime | None


class DeviceCreateResponse(BaseModel):
    """Returned once when a device is created.

    ``enrollment_secret`` is the plaintext one-time credential. It is shown here
    exactly once and only stored hashed on the server; it cannot be retrieved
    again.
    """

    device: DeviceOut
    enrollment_secret: str
