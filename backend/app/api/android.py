"""Admin endpoints for Android (Android Management API) management.

Status is always available. The live endpoints (devices, enrollment token,
commands) require the integration to be configured; otherwise they return 503
with guidance. See docs/android-feasibility.md.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import SessionDep, client_ip, require_permission
from app.core import android as amapi
from app.core.audit import record_action
from app.models.admin import Admin
from app.models.enums import Permission
from app.schemas.android import (
    AndroidCommandIn,
    AndroidStatusOut,
    EnrollmentTokenOut,
)

router = APIRouter(prefix="/android", tags=["android"])

ViewDevices = Annotated[Admin, Depends(require_permission(Permission.VIEW_DEVICES))]
ManageDevices = Annotated[Admin, Depends(require_permission(Permission.MANAGE_DEVICES))]

_NOT_CONFIGURED = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail=(
        "Android management is not configured. Set ANDROID_PROJECT_ID, "
        "ANDROID_ENTERPRISE_NAME and ANDROID_SA_JSON. See docs/android-feasibility.md."
    ),
)


@router.get("/status", response_model=AndroidStatusOut)
async def android_status(admin: ViewDevices):
    cfg = amapi.get_android_config()
    return AndroidStatusOut(
        configured=cfg is not None,
        project_id=cfg.project_id if cfg else None,
        enterprise_name=cfg.enterprise_name if cfg else None,
        capabilities=amapi.CAPABILITIES,
        commands=sorted(amapi.VALID_COMMANDS),
    )


@router.get("/devices")
async def android_devices(admin: ViewDevices):
    try:
        client = amapi.get_client()
    except amapi.AndroidNotConfigured:
        raise _NOT_CONFIGURED from None
    try:
        return client.list_devices()
    except amapi.AndroidApiError as exc:
        raise HTTPException(status_code=502, detail=f"Android API error: {exc}") from None


@router.post("/enrollment-token", response_model=EnrollmentTokenOut)
async def android_enrollment_token(
    request: Request, session: SessionDep, admin: ManageDevices
):
    try:
        client = amapi.get_client()
    except amapi.AndroidNotConfigured:
        raise _NOT_CONFIGURED from None
    try:
        token = client.create_enrollment_token()
    except amapi.AndroidApiError as exc:
        raise HTTPException(status_code=502, detail=f"Android API error: {exc}") from None
    await record_action(
        session,
        action="android.enrollment_token",
        actor=admin,
        target_type="android_enterprise",
        ip_address=client_ip(request),
    )
    return EnrollmentTokenOut(
        name=token.get("name"),
        value=token.get("value"),
        qr_code=token.get("qrCode"),
    )


@router.post("/command")
async def android_command(
    payload: AndroidCommandIn, request: Request, session: SessionDep, admin: ManageDevices
):
    if payload.type not in amapi.VALID_COMMANDS:
        raise HTTPException(status_code=422, detail="Unsupported command type")
    try:
        client = amapi.get_client()
    except amapi.AndroidNotConfigured:
        raise _NOT_CONFIGURED from None
    try:
        result = client.issue_command(payload.device_name, payload.type)
    except amapi.AndroidApiError as exc:
        raise HTTPException(status_code=502, detail=f"Android API error: {exc}") from None
    await record_action(
        session,
        action="android.command",
        actor=admin,
        target_type="android_device",
        target_id=payload.device_name,
        detail=f"type={payload.type}",
        ip_address=client_ip(request),
    )
    return result
