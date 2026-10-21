"""Schemas for the Apple MDM endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AppleStatusOut(BaseModel):
    configured: bool
    server_url: str | None = None
    push_topic: str | None = None
    capabilities: dict[str, Any]
    enrollment_models: list[dict[str, Any]]
