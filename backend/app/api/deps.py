"""Shared API dependencies: current admin and permission checks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.database import get_session
from app.core.security import TokenError, decode_token
from app.models.admin import Admin
from app.models.device import Device
from app.models.enums import EnrollmentStatus, Permission

# auto_error=False so we can return a consistent 401 with a WWW-Authenticate
# header rather than FastAPI's default.
_bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def client_ip(request: Request) -> str:
    """Best-effort client IP (handles a single proxy via X-Forwarded-For)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def get_current_admin(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Admin:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not credentials.credentials:
        raise unauthorized
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except TokenError:
        raise unauthorized from None

    admin = await session.get(Admin, int(payload["sub"]))
    if admin is None or not admin.is_active:
        raise unauthorized
    return admin


CurrentAdmin = Annotated[Admin, Depends(get_current_admin)]


async def get_current_device(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Device:
    """Authenticate a device agent by its device token.

    Rejects unknown devices and any device that is not currently enrolled
    (e.g. revoked), so a revoked device cannot submit data.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Device not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not credentials.credentials:
        raise unauthorized
    try:
        payload = decode_token(credentials.credentials, expected_type="device")
    except TokenError:
        raise unauthorized from None

    result = await session.execute(
        select(Device).where(Device.device_uid == payload["sub"])
    )
    device = result.scalar_one_or_none()
    if device is None or device.enrollment_status != EnrollmentStatus.ENROLLED:
        raise unauthorized
    return device


CurrentDevice = Annotated[Device, Depends(get_current_device)]


def require_permission(permission: Permission) -> Callable[[Admin], Admin]:
    """Dependency factory: require the current admin to hold ``permission``."""

    async def checker(admin: CurrentAdmin) -> Admin:
        if not admin.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission.value}",
            )
        return admin

    return checker
