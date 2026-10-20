"""Authorized live remote-support sessions.

A session records who started it and when, shows as active to the device (which
then captures near-live snapshots and displays a consent indicator), and can be
ended by an authorized admin. Sessions are not recorded beyond the snapshots the
viewer sees, and those follow the normal screenshot retention policy.

Access rules:
- Start / end a session: initiate_live_session
- List / view sessions: view_devices
- View a session's snapshots: view_screenshots
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import SessionDep, client_ip, require_permission
from app.core.audit import record_action
from app.models.admin import Admin
from app.models.device import Device
from app.models.enums import Permission
from app.models.monitoring import RemoteSession, Screenshot
from app.schemas.monitoring import RemoteSessionOut, ScreenshotOut

router = APIRouter(tags=["remote-support"])

InitiateSession = Annotated[
    Admin, Depends(require_permission(Permission.INITIATE_LIVE_SESSION))
]
ViewDevices = Annotated[Admin, Depends(require_permission(Permission.VIEW_DEVICES))]
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


@router.post(
    "/devices/{device_uid}/sessions",
    response_model=RemoteSessionOut,
    status_code=status.HTTP_201_CREATED,
)
async def start_session(
    device_uid: str, request: Request, session: SessionDep, admin: InitiateSession
):
    device = await _device_or_404(session, device_uid)
    # Reuse an already-active session rather than stacking them.
    active = await session.scalar(
        select(RemoteSession).where(
            RemoteSession.device_id == device.id, RemoteSession.status == "active"
        )
    )
    if active is not None:
        return active

    remote = RemoteSession(
        device_id=device.id,
        initiated_by_admin_id=admin.id,
        initiated_by_email=admin.email,
        status="active",
    )
    session.add(remote)
    await record_action(
        session,
        action="session.start",
        actor=admin,
        target_type="device",
        target_id=device.device_uid,
        ip_address=client_ip(request),
        commit=False,
    )
    await session.commit()
    await session.refresh(remote)
    return remote


@router.get("/devices/{device_uid}/sessions", response_model=list[RemoteSessionOut])
async def list_sessions(device_uid: str, session: SessionDep, admin: ViewDevices):
    device = await _device_or_404(session, device_uid)
    rows = (
        await session.execute(
            select(RemoteSession)
            .where(RemoteSession.device_id == device.id)
            .order_by(RemoteSession.started_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return list(rows)


@router.post("/sessions/{session_id}/end", response_model=RemoteSessionOut)
async def end_session(
    session_id: int, request: Request, session: SessionDep, admin: InitiateSession
):
    remote = await session.get(RemoteSession, session_id)
    if remote is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if remote.status == "active":
        remote.status = "ended"
        remote.ended_at = datetime.now(timezone.utc)
        remote.end_reason = "admin_ended"
        await record_action(
            session,
            action="session.end",
            actor=admin,
            target_type="session",
            target_id=str(session_id),
            ip_address=client_ip(request),
            commit=False,
        )
        await session.commit()
        await session.refresh(remote)
    return remote


@router.get("/sessions/{session_id}/screenshots", response_model=list[ScreenshotOut])
async def session_screenshots(
    session_id: int, session: SessionDep, admin: ViewScreenshots
):
    remote = await session.get(RemoteSession, session_id)
    if remote is None:
        raise HTTPException(status_code=404, detail="Session not found")
    rows = (
        await session.execute(
            select(Screenshot)
            .where(Screenshot.session_id == session_id)
            .order_by(Screenshot.captured_at.desc())
            .limit(30)
        )
    ).scalars().all()
    return list(rows)
