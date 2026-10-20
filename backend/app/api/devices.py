"""Device management routes (admin-facing).

Agent-facing enrollment and heartbeat arrive in Milestone 4. Here an admin can
create a device record (which mints a one-time enrollment secret), list and view
devices, revoke access, and delete a device and its record.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import SessionDep, client_ip, require_permission
from app.core.audit import record_action
from app.core.security import (
    generate_device_uid,
    generate_enrollment_secret,
    hash_secret,
)
from app.models.admin import Admin
from app.models.device import Device
from app.models.enums import EnrollmentStatus, Permission
from app.schemas.device import DeviceCreate, DeviceCreateResponse, DeviceOut

router = APIRouter(prefix="/devices", tags=["devices"])

ManageDevices = Annotated[Admin, Depends(require_permission(Permission.MANAGE_DEVICES))]
ViewDevices = Annotated[Admin, Depends(require_permission(Permission.VIEW_DEVICES))]


async def _get_or_404(session: SessionDep, device_uid: str) -> Device:
    result = await session.execute(
        select(Device).where(Device.device_uid == device_uid)
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.post(
    "", response_model=DeviceCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_device(
    payload: DeviceCreate, request: Request, session: SessionDep, admin: ManageDevices
):
    secret = generate_enrollment_secret()
    device = Device(
        device_uid=generate_device_uid(),
        name=payload.name,
        os_type=payload.os_type,
        device_type=payload.device_type,
        assigned_to=payload.assigned_to,
        enrollment_status=EnrollmentStatus.PENDING,
        enrollment_secret_hash=hash_secret(secret),
        enrolled_by_admin_id=admin.id,
    )
    session.add(device)
    await session.flush()  # assign device.id
    await record_action(
        session,
        action="device.create",
        actor=admin,
        target_type="device",
        target_id=device.device_uid,
        detail=f"os={payload.os_type.value} type={payload.device_type.value}",
        ip_address=client_ip(request),
        commit=False,
    )
    await session.commit()
    await session.refresh(device)
    # The plaintext secret is returned exactly once and never stored.
    return DeviceCreateResponse(
        device=DeviceOut.model_validate(device), enrollment_secret=secret
    )


@router.get("", response_model=list[DeviceOut])
async def list_devices(session: SessionDep, admin: ViewDevices):
    result = await session.execute(select(Device).order_by(Device.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{device_uid}", response_model=DeviceOut)
async def get_device(device_uid: str, session: SessionDep, admin: ViewDevices):
    return await _get_or_404(session, device_uid)


@router.post("/{device_uid}/revoke", response_model=DeviceOut)
async def revoke_device(
    device_uid: str, request: Request, session: SessionDep, admin: ManageDevices
):
    device = await _get_or_404(session, device_uid)
    device.enrollment_status = EnrollmentStatus.REVOKED
    await record_action(
        session,
        action="device.revoke",
        actor=admin,
        target_type="device",
        target_id=device.device_uid,
        ip_address=client_ip(request),
        commit=False,
    )
    await session.commit()
    await session.refresh(device)
    return device


@router.delete("/{device_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_uid: str, request: Request, session: SessionDep, admin: ManageDevices
):
    device = await _get_or_404(session, device_uid)
    uid = device.device_uid
    await session.delete(device)
    await record_action(
        session,
        action="device.delete",
        actor=admin,
        target_type="device",
        target_id=uid,
        ip_address=client_ip(request),
        commit=False,
    )
    await session.commit()
