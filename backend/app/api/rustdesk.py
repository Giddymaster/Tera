"""Admin endpoint to retrieve a device's RustDesk connection details.

The unattended password is sensitive, so retrieval requires the live-session
permission and is audit-logged.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import SessionDep, client_ip, require_permission
from app.core.audit import record_action
from app.core.config import get_settings
from app.core.encryption import decrypt_bytes
from app.models.admin import Admin
from app.models.device import Device
from app.models.enums import Permission

settings = get_settings()
router = APIRouter(tags=["rustdesk"])

InitiateSession = Annotated[
    Admin, Depends(require_permission(Permission.INITIATE_LIVE_SESSION))
]


@router.get("/devices/{device_uid}/rustdesk")
async def get_rustdesk(
    device_uid: str, request: Request, session: SessionDep, admin: InitiateSession
):
    device = await session.scalar(
        select(Device).where(Device.device_uid == device_uid)
    )
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    if not device.rustdesk_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This device has not reported RustDesk yet.",
        )

    password = None
    if device.rustdesk_password_enc:
        try:
            password = decrypt_bytes(device.rustdesk_password_enc.encode()).decode()
        except ValueError:
            password = None

    await record_action(
        session,
        action="rustdesk.credential_view",
        actor=admin,
        target_type="device",
        target_id=device.device_uid,
        ip_address=client_ip(request),
    )
    return {
        "rustdesk_id": device.rustdesk_id,
        "password": password,
        "host": settings.rustdesk_host,
        "key": settings.rustdesk_key,
        "enabled": bool(settings.rustdesk_host),
    }
