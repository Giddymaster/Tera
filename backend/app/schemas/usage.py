"""Application-usage schemas (agent submission and admin summary)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

# One day's worth of seconds, with a little slack. Guards against bad input.
_MAX_SECONDS_PER_ENTRY = 60 * 60 * 24 + 3600


class UsageEntry(BaseModel):
    app_name: str = Field(min_length=1, max_length=120)
    seconds: int = Field(ge=0, le=_MAX_SECONDS_PER_ENTRY)
    # Defaults to the server's current UTC day if the agent omits it.
    day: date | None = None


class UsageReportRequest(BaseModel):
    entries: list[UsageEntry] = Field(min_length=1, max_length=500)


class AppUsageOut(BaseModel):
    app_name: str
    seconds: int


class DeviceUsageOut(BaseModel):
    device_uid: str
    days: int
    total_seconds: int
    apps: list[AppUsageOut]
