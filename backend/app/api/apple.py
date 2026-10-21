"""Admin endpoints for Apple (iOS/iPadOS) MDM status.

Only a status + capability surface is exposed. A live MDM server integration is a
substantial separate system and is not implemented here; see
docs/apple-mdm-feasibility.md.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import require_permission
from app.core import apple
from app.models.admin import Admin
from app.models.enums import Permission
from app.schemas.apple import AppleStatusOut

router = APIRouter(prefix="/apple", tags=["apple"])

ViewDevices = Annotated[Admin, Depends(require_permission(Permission.VIEW_DEVICES))]


@router.get("/status", response_model=AppleStatusOut)
async def apple_status(admin: ViewDevices):
    cfg = apple.get_apple_config()
    return AppleStatusOut(
        configured=cfg is not None,
        server_url=cfg.server_url if cfg else None,
        push_topic=cfg.push_topic if cfg else None,
        capabilities=apple.CAPABILITIES,
        enrollment_models=apple.ENROLLMENT_MODELS,
    )
