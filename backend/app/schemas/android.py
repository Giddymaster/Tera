"""Schemas for the Android management endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AndroidStatusOut(BaseModel):
    configured: bool
    project_id: str | None = None
    enterprise_name: str | None = None
    capabilities: dict[str, Any]
    commands: list[str]


class EnrollmentTokenOut(BaseModel):
    # Subset of the AMAPI enrollment token: the value and QR payload the admin
    # uses to enroll a device.
    name: str | None = None
    value: str | None = None
    qr_code: str | None = None


class AndroidCommandIn(BaseModel):
    device_name: str = Field(min_length=1, max_length=300)
    type: str = Field(min_length=1, max_length=40)
