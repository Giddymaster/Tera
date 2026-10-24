"""Admin endpoints for screenshot policy, capture requests, and viewing images.

Access rules:
- Reading the policy: view_devices
- Changing the policy: manage_security_policy
- Requesting a capture, listing, viewing, and deleting images: view_screenshots
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import delete, func, select

from app.api.deps import SessionDep, client_ip, require_permission
from app.core.audit import record_action
from app.core.screenshots import delete_blob, load_decrypted
from app.models.admin import Admin
from app.models.device import Device
from app.models.enums import Permission
from app.models.monitoring import CaptureRequest, Screenshot, ScreenshotPolicy
from app.schemas.monitoring import (
    ScreenshotOut,
    ScreenshotPolicyIn,
    ScreenshotPolicyOut,
)

router = APIRouter(tags=["screenshots"])

ViewDevices = Annotated[Admin, Depends(require_permission(Permission.VIEW_DEVICES))]
ManagePolicy = Annotated[
    Admin, Depends(require_permission(Permission.MANAGE_SECURITY_POLICY))
]
ViewScreenshots = Annotated[
    Admin, Depends(require_permission(Permission.VIEW_SCREENSHOTS))
]


async def _device_or_404(session: SessionDep, device_uid: str) -> Device:
    device = await session.scalar(
        select(Device).where(Device.device_uid == device_uid)
    )
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


async def _policy_for(session: SessionDep, device: Device) -> ScreenshotPolicy:
    policy = await session.scalar(
        select(ScreenshotPolicy).where(ScreenshotPolicy.device_id == device.id)
    )
    if policy is None:
        policy = ScreenshotPolicy(device_id=device.id)
        session.add(policy)
        await session.commit()
        await session.refresh(policy)
    return policy


@router.get("/devices/{device_uid}/screenshot-policy", response_model=ScreenshotPolicyOut)
async def get_policy(device_uid: str, session: SessionDep, admin: ViewDevices):
    device = await _device_or_404(session, device_uid)
    return await _policy_for(session, device)


@router.put("/devices/{device_uid}/screenshot-policy", response_model=ScreenshotPolicyOut)
async def update_policy(
    device_uid: str,
    payload: ScreenshotPolicyIn,
    request: Request,
    session: SessionDep,
    admin: ManagePolicy,
):
    device = await _device_or_404(session, device_uid)
    policy = await _policy_for(session, device)
    for field, value in payload.model_dump().items():
        setattr(policy, field, value)
    await record_action(
        session,
        action="screenshot.policy_update",
        actor=admin,
        target_type="device",
        target_id=device.device_uid,
        detail=f"enabled={payload.enabled} interval={payload.interval_minutes}m",
        ip_address=client_ip(request),
        commit=False,
    )
    await session.commit()
    await session.refresh(policy)
    return policy


@router.post(
    "/devices/{device_uid}/screenshots/request", status_code=status.HTTP_202_ACCEPTED
)
async def request_capture(
    device_uid: str, request: Request, session: SessionDep, admin: ViewScreenshots
):
    device = await _device_or_404(session, device_uid)
    session.add(
        CaptureRequest(device_id=device.id, requested_by_admin_id=admin.id)
    )
    await record_action(
        session,
        action="screenshot.request",
        actor=admin,
        target_type="device",
        target_id=device.device_uid,
        ip_address=client_ip(request),
        commit=False,
    )
    await session.commit()
    return {"status": "requested"}


@router.get("/devices/{device_uid}/screenshots", response_model=list[ScreenshotOut])
async def list_screenshots(
    device_uid: str,
    session: SessionDep,
    admin: ViewScreenshots,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    device = await _device_or_404(session, device_uid)
    rows = (
        await session.execute(
            select(Screenshot)
            .where(Screenshot.device_id == device.id)
            .order_by(Screenshot.captured_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return list(rows)


@router.get("/devices/{device_uid}/screenshots/count")
async def count_screenshots(
    device_uid: str, session: SessionDep, admin: ViewScreenshots
):
    device = await _device_or_404(session, device_uid)
    total = await session.scalar(
        select(func.count()).select_from(Screenshot).where(
            Screenshot.device_id == device.id
        )
    )
    return {"count": int(total or 0)}


@router.delete(
    "/devices/{device_uid}/screenshots", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_all_screenshots(
    device_uid: str, request: Request, session: SessionDep, admin: ViewScreenshots
):
    """Delete every screenshot for a device (files on disk and rows)."""
    device = await _device_or_404(session, device_uid)
    rows = (
        await session.execute(
            select(Screenshot).where(Screenshot.device_id == device.id)
        )
    ).scalars().all()
    for row in rows:
        delete_blob(row.storage_path)
    await session.execute(
        delete(Screenshot).where(Screenshot.device_id == device.id)
    )
    await record_action(
        session,
        action="screenshot.delete_all",
        actor=admin,
        target_type="device",
        target_id=device.device_uid,
        detail=f"count={len(rows)}",
        ip_address=client_ip(request),
        commit=False,
    )
    await session.commit()


@router.get("/screenshots/{screenshot_id}/image")
async def get_screenshot_image(
    screenshot_id: int, session: SessionDep, admin: ViewScreenshots
):
    shot = await session.get(Screenshot, screenshot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    try:
        data = load_decrypted(shot.storage_path)
    except (FileNotFoundError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Image unavailable"
        ) from None
    return Response(content=data, media_type="image/jpeg")


@router.delete("/screenshots/{screenshot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_screenshot(
    screenshot_id: int, request: Request, session: SessionDep, admin: ViewScreenshots
):
    shot = await session.get(Screenshot, screenshot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    delete_blob(shot.storage_path)
    await session.delete(shot)
    await record_action(
        session,
        action="screenshot.delete",
        actor=admin,
        target_type="screenshot",
        target_id=str(screenshot_id),
        ip_address=client_ip(request),
        commit=False,
    )
    await session.commit()
