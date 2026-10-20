"""Authentication request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Role


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
