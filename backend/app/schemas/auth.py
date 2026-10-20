"""Authentication request/response schemas."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.enums import Role


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


class LoginRequest(BaseModel):
    # Plain str rather than EmailStr to avoid an extra dependency; the value is
    # only ever used for an exact lookup, never interpolated anywhere unsafe.
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=4096)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access-token lifetime in seconds


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: Role
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None
    permissions: list[str] = Field(default_factory=list)

    @field_serializer("created_at", "last_login_at")
    def _ser_dt(self, value: datetime | None) -> str | None:
        return _iso_utc(value)
