"""Schemas for screenshot policy, screenshots, remote sessions, and directives."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
#  Policy
# --------------------------------------------------------------------------- #
class ScreenshotPolicyIn(BaseModel):
    enabled: bool = False
    interval_minutes: int = Field(default=15, ge=1, le=1440)
    active_hour_start: int | None = Field(default=None, ge=0, le=23)
    active_hour_end: int | None = Field(default=None, ge=0, le=23)
    retention_days: int = Field(default=30, ge=1, le=365)
    excluded_apps: str | None = Field(default=None, max_length=2000)


class ScreenshotPolicyOut(ScreenshotPolicyIn):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
#  Screenshots
# --------------------------------------------------------------------------- #
class ScreenshotUploadIn(BaseModel):
    image_base64: str = Field(min_length=1)
    trigger: Literal["schedule", "request", "session"] = "schedule"
    foreground_app: str | None = Field(default=None, max_length=120)
    session_id: int | None = None
    width: int = Field(default=0, ge=0)
    height: int = Field(default=0, ge=0)


class ScreenshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    captured_at: datetime
    trigger: str
    session_id: int | None
    foreground_app: str | None
    width: int
    height: int
    size_bytes: int

    @field_serializer("captured_at")
    def _ser_dt(self, value: datetime) -> str | None:
        return _iso_utc(value)


# --------------------------------------------------------------------------- #
#  Remote sessions
# --------------------------------------------------------------------------- #
class RemoteSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    initiated_by_email: str | None
    started_at: datetime
    ended_at: datetime | None
    end_reason: str | None

    @field_serializer("started_at", "ended_at")
    def _ser_dt(self, value: datetime | None) -> str | None:
        return _iso_utc(value)


# --------------------------------------------------------------------------- #
#  Agent directives (what the device should do right now)
# --------------------------------------------------------------------------- #
class DirectivePolicy(BaseModel):
    enabled: bool
    interval_minutes: int
    active_hour_start: int | None
    active_hour_end: int | None
    excluded_apps: list[str]


class DirectiveRustDesk(BaseModel):
    enabled: bool = False
    host: str = ""
    key: str = ""


class DirectivesOut(BaseModel):
    screenshot_policy: DirectivePolicy
    capture_requested: bool
    session_active: bool
    session_id: int | None
    session_capture_interval_seconds: int
    location_enabled: bool = False
    location_requested: bool = False
    rustdesk: DirectiveRustDesk = DirectiveRustDesk()


# --------------------------------------------------------------------------- #
#  Location
# --------------------------------------------------------------------------- #
class LocationPolicyIn(BaseModel):
    enabled: bool = False
    retention_days: int = Field(default=30, ge=1, le=365)


class LocationPolicyOut(LocationPolicyIn):
    model_config = ConfigDict(from_attributes=True)


class LocationReportIn(BaseModel):
    # The agent reports a status; coordinates are present only when status == "ok".
    status: Literal["ok", "unavailable", "permission_restricted"]
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0)
    source: str = Field(default="windows_agent", max_length=32)


class LocationPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    captured_at: datetime
    latitude: float
    longitude: float
    accuracy_m: float | None
    source: str

    @field_serializer("captured_at")
    def _ser_dt(self, value: datetime) -> str | None:
        return _iso_utc(value)


class LocationOut(BaseModel):
    enabled: bool
    # "current" (recent fix), "stale" (old fix), or "none" (no stored fix)
    freshness: str
    latest: LocationPointOut | None
    history: list[LocationPointOut]
