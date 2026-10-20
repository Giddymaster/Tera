"""Device request/response schemas."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.enums import DeviceType, EnrollmentStatus, OSType


def _iso_utc(value: datetime | None) -> str | None:
    """Serialize a datetime as an explicit-UTC ISO string.

    SQLite stores datetimes without timezone info, so values read back are
    naive. We treat them as UTC and emit an offset so browsers parse them
    correctly regardless of the viewer's local timezone.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


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

    @field_serializer("created_at", "updated_at", "last_seen_at")
    def _ser_dt(self, value: datetime | None) -> str | None:
        return _iso_utc(value)


class DeviceCreateResponse(BaseModel):
    """Returned once when a device is created.

    ``enrollment_secret`` is the plaintext one-time credential. It is shown here
    exactly once and only stored hashed on the server; it cannot be retrieved
    again.
    """

    device: DeviceOut
    enrollment_secret: str
