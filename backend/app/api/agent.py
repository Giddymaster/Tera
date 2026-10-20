"""Device-agent routes: enrollment and heartbeat.

These are the only endpoints a device agent calls. Admin endpoints live
elsewhere and use a different token type, so a device token cannot be used to
act as an admin and vice versa.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentDevice, SessionDep, client_ip
from app.core.audit import record_action
from app.core.config import get_settings
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import create_device_token, verify_secret
from app.models.device import Device
from app.models.enums import EnrollmentStatus
from app.models.usage import AppUsage
from app.schemas.agent import (
    EnrollRequest,
    EnrollResponse,
    HeartbeatRequest,
    HeartbeatResponse,
)
from app.schemas.device import DeviceOut
from app.schemas.usage import UsageReportRequest

settings = get_settings()
router = APIRouter(prefix="/agent", tags=["agent"])

# Per-IP limiter to slow brute-forcing of enrollment secrets.
enroll_limiter = SlidingWindowLimiter(
    max_attempts=settings.login_max_attempts,
    window_seconds=settings.login_window_seconds,
)


@router.post("/enroll", response_model=EnrollResponse)
async def enroll(payload: EnrollRequest, request: Request, session: SessionDep):
    ip = client_ip(request)
    if not enroll_limiter.is_allowed(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many enrollment attempts. Please wait and try again.",
            headers={"Retry-After": str(enroll_limiter.retry_after(ip))},
        )

    result = await session.execute(
        select(Device).where(Device.device_uid == payload.device_uid)
    )
    device = result.scalar_one_or_none()

    # One identical failure for every bad case so the endpoint reveals nothing
    # about which device ids exist or their state.
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid device id or enrollment secret",
    )

    secret_ok = device is not None and verify_secret(
        device.enrollment_secret_hash, payload.enrollment_secret
    )
    # Enrollment is single-use: only a device still pending can enroll.
    if (
        device is None
        or device.enrollment_status != EnrollmentStatus.PENDING
        or not secret_ok
    ):
        await record_action(
            session,
            action="device.enroll_failed",
            target_type="device",
            target_id=payload.device_uid,
            ip_address=ip,
        )
        raise invalid

    device.enrollment_status = EnrollmentStatus.ENROLLED
    device.last_seen_at = datetime.now(timezone.utc)
    await record_action(
        session,
        action="device.enroll",
        target_type="device",
        target_id=device.device_uid,
        ip_address=ip,
        commit=False,
    )
    await session.commit()
    await session.refresh(device)

    return EnrollResponse(
        device_token=create_device_token(device.device_uid),
        device=DeviceOut.model_validate(device),
    )


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(
    payload: HeartbeatRequest, session: SessionDep, device: CurrentDevice
):
    now = datetime.now(timezone.utc)
    device.last_seen_at = now
    if payload.agent_version is not None:
        device.agent_version = payload.agent_version
    if payload.os_version is not None:
        device.os_version = payload.os_version
    if payload.disk_free_gb is not None:
        device.disk_free_gb = payload.disk_free_gb
    if payload.disk_total_gb is not None:
        device.disk_total_gb = payload.disk_total_gb
    if payload.battery_percent is not None:
        device.battery_percent = payload.battery_percent
    if payload.power_plugged is not None:
        device.power_plugged = payload.power_plugged
    await session.commit()

    return HeartbeatResponse(
        enrollment_status=device.enrollment_status.value,
        last_seen_at=now,
        server_time=now,
    )


@router.post("/usage", status_code=status.HTTP_204_NO_CONTENT)
async def report_usage(
    payload: UsageReportRequest, session: SessionDep, device: CurrentDevice
):
    """Merge foreground app-usage entries (app name + seconds) for this device.

    Durations accumulate per app per day. No window titles, URLs, or content are
    accepted or stored.
    """
    today = datetime.now(timezone.utc).date()
    for entry in payload.entries:
        day = entry.day or today
        existing = await session.scalar(
            select(AppUsage).where(
                AppUsage.device_id == device.id,
                AppUsage.app_name == entry.app_name,
                AppUsage.day == day,
            )
        )
        if existing is None:
            session.add(
                AppUsage(
                    device_id=device.id,
                    app_name=entry.app_name,
                    day=day,
                    seconds=entry.seconds,
                )
            )
        else:
            existing.seconds += entry.seconds
    await session.commit()
