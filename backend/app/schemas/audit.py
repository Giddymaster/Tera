"""Audit-log response schema."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    actor_email: str | None
    action: str
    target_type: str | None
    target_id: str | None
    detail: str | None
    ip_address: str | None

    @field_serializer("timestamp")
    def _ser_dt(self, value: datetime) -> str | None:
        return _iso_utc(value)
