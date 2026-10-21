"""Admin endpoints for device location: policy, on-demand request, and history.

Location history is restricted to admins with view_reports. Every result carries
its source and timestamp and a freshness indicator. A location is shown only when
a real fix exists; otherwise the UI shows "unavailable" rather than a coordinate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import SessionDep, client_ip, require_permission
from app.core.audit import record_action
from app.core.location import CURRENT_THRESHOLD_SECONDS, delete_expired
from app.models.admin import Admin
from app.models.device import Device
from app.models.enums import Permission
from app.models.monitoring import LocationPoint, LocationPolicy
from app.schemas.monitoring import (
    LocationOut,
    LocationPointOut,
    LocationPolicyIn,
    LocationPolicyOut,
)

router = APIRouter(tags=["location"])

ViewReports = Annotated[Admin, Depends(require_permission(Permission.VIEW_REPORTS))]
ManagePolicy = Annotated[
    Admin, Depends(require_permission(Permission.MANAGE_SECURITY_POLICY))
]
ManageDevices = Annotated[Admin, Depends(require_permission(Permission.MANAGE_DEVICES))]


async def _device_or_404(session: SessionDep, device_uid: str) -> Device:
    device = await session.scalar(
        select(Device).where(Device.device_uid == device_uid)
    )
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


async def _policy_for(session: SessionDep, device: Device) -> LocationPolicy:
    policy = await session.scalar(
        select(LocationPolicy).where(LocationPolicy.device_id == device.id)
    )
    if policy is None:
        policy = LocationPolicy(device_id=device.id)
        session.add(policy)
        await session.commit()
        await session.refresh(policy)
    return policy


@router.get("/devices/{device_uid}/location", response_model=LocationOut)
async def get_location(device_uid: str, session: SessionDep, admin: ViewReports):
    device = await _device_or_404(session, device_uid)
    policy = await _policy_for(session, device)
    await delete_expired(session)

    rows = (
        await session.execute(
            select(LocationPoint)
            .where(LocationPoint.device_id == device.id)
            .order_by(LocationPoint.captured_at.desc())
            .limit(50)
        )
    ).scalars().all()

    latest = rows[0] if rows else None
    if latest is None:
        freshness = "none"
    else:
        captured = latest.captured_at
        if captured.tzinfo is None:
            captured = captured.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - captured).total_seconds()
        freshness = "current" if age <= CURRENT_THRESHOLD_SECONDS else "stale"

    return LocationOut(
        enabled=policy.enabled,
        freshness=freshness,
        latest=LocationPointOut.model_validate(latest) if latest else None,
        history=[LocationPointOut.model_validate(r) for r in rows],
    )


@router.put("/devices/{device_uid}/location-policy", response_model=LocationPolicyOut)
async def update_location_policy(
    device_uid: str,
    payload: LocationPolicyIn,
    request: Request,
    session: SessionDep,
    admin: ManagePolicy,
):
    device = await _device_or_404(session, device_uid)
    policy = await _policy_for(session, device)
    policy.enabled = payload.enabled
    policy.retention_days = payload.retention_days
    await record_action(
        session,
        action="location.policy_update",
        actor=admin,
        target_type="device",
        target_id=device.device_uid,
        detail=f"enabled={payload.enabled}",
        ip_address=client_ip(request),
        commit=False,
    )
    await session.commit()
    await session.refresh(policy)
    return policy


@router.post(
    "/devices/{device_uid}/location/request", status_code=status.HTTP_202_ACCEPTED
)
async def request_location(
    device_uid: str, request: Request, session: SessionDep, admin: ManageDevices
):
    device = await _device_or_404(session, device_uid)
    policy = await _policy_for(session, device)
    policy.requested_at = datetime.now(timezone.utc)
    await record_action(
        session,
        action="location.request",
        actor=admin,
        target_type="device",
        target_id=device.device_uid,
        ip_address=client_ip(request),
        commit=False,
    )
    await session.commit()
    return {"status": "requested"}
