"""Device-agent routes: enrollment and heartbeat.

These are the only endpoints a device agent calls. Admin endpoints live
elsewhere and use a different token type, so a device token cannot be used to
act as an admin and vice versa.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from app.api.deps import CurrentDevice, SessionDep, client_ip
from app.core.audit import record_action
from app.core.config import get_settings
from app.core.rate_limit import SlidingWindowLimiter
from app.core.screenshots import delete_expired, save_encrypted
from app.core.security import create_device_token, verify_secret
from app.models.device import Device
from app.models.enums import EnrollmentStatus
from app.models.monitoring import (
    CaptureRequest,
    LocationPoint,
    LocationPolicy,
    RemoteSession,
    Screenshot,
    ScreenshotPolicy,
)
from app.models.usage import AppUsage
from app.schemas.agent import (
    EnrollRequest,
    EnrollResponse,
    HeartbeatRequest,
    HeartbeatResponse,
)
from app.schemas.device import DeviceOut
from app.schemas.monitoring import (
    DirectivePolicy,
    DirectivesOut,
    LocationReportIn,
    ScreenshotOut,
    ScreenshotUploadIn,
)
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

    reported = payload.agent_version or device.agent_version
    latest = settings.agent_latest_version
    return HeartbeatResponse(
        enrollment_status=device.enrollment_status.value,
        last_seen_at=now,
        server_time=now,
        latest_agent_version=latest,
        update_available=reported is not None and reported != latest,
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


@router.get("/directives", response_model=DirectivesOut)
async def directives(session: SessionDep, device: CurrentDevice):
    """Tell the agent what to do now: screenshot policy, pending captures, and
    whether a live-support session is active."""
    policy = await session.scalar(
        select(ScreenshotPolicy).where(ScreenshotPolicy.device_id == device.id)
    )
    pending = await session.scalar(
        select(func.count())
        .select_from(CaptureRequest)
        .where(
            CaptureRequest.device_id == device.id,
            CaptureRequest.fulfilled_at.is_(None),
        )
    )
    active = await session.scalar(
        select(RemoteSession)
        .where(RemoteSession.device_id == device.id, RemoteSession.status == "active")
        .order_by(RemoteSession.started_at.desc())
    )
    loc_policy = await session.scalar(
        select(LocationPolicy).where(LocationPolicy.device_id == device.id)
    )
    excluded = [
        a.strip()
        for a in ((policy.excluded_apps or "").split(",") if policy else [])
        if a.strip()
    ]
    dp = DirectivePolicy(
        enabled=policy.enabled if policy else False,
        interval_minutes=policy.interval_minutes if policy else 15,
        active_hour_start=policy.active_hour_start if policy else None,
        active_hour_end=policy.active_hour_end if policy else None,
        excluded_apps=excluded,
    )
    return DirectivesOut(
        screenshot_policy=dp,
        capture_requested=bool(pending),
        session_active=active is not None,
        session_id=active.id if active else None,
        session_capture_interval_seconds=settings.session_capture_interval_seconds,
        location_enabled=bool(loc_policy.enabled) if loc_policy else False,
        location_requested=bool(loc_policy.requested_at) if loc_policy else False,
    )


@router.post(
    "/screenshot", response_model=ScreenshotOut, status_code=status.HTTP_201_CREATED
)
async def upload_screenshot(
    payload: ScreenshotUploadIn, session: SessionDep, device: CurrentDevice
):
    try:
        raw = base64.b64decode(payload.image_base64, validate=True)
    except Exception:  # noqa: BLE001 - any decode error is a bad request
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image encoding"
        ) from None
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image"
        )
    if len(raw) > settings.max_screenshot_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Screenshot too large",
        )

    policy = await session.scalar(
        select(ScreenshotPolicy).where(ScreenshotPolicy.device_id == device.id)
    )
    retention_days = policy.retention_days if policy else 30

    requested_by = None
    if payload.trigger == "request":
        req = await session.scalar(
            select(CaptureRequest)
            .where(
                CaptureRequest.device_id == device.id,
                CaptureRequest.fulfilled_at.is_(None),
            )
            .order_by(CaptureRequest.created_at.asc())
        )
        if req is not None:
            req.fulfilled_at = datetime.now(timezone.utc)
            requested_by = req.requested_by_admin_id

    session_id = None
    if payload.trigger == "session" and payload.session_id is not None:
        sess = await session.get(RemoteSession, payload.session_id)
        if sess is not None and sess.device_id == device.id and sess.status == "active":
            session_id = sess.id

    storage_path = save_encrypted(device.device_uid, raw)
    now = datetime.now(timezone.utc)
    shot = Screenshot(
        device_id=device.id,
        captured_at=now,
        trigger=payload.trigger,
        requested_by_admin_id=requested_by,
        session_id=session_id,
        foreground_app=payload.foreground_app,
        width=payload.width,
        height=payload.height,
        size_bytes=len(raw),
        storage_path=storage_path,
        retention_until=now + timedelta(days=retention_days),
    )
    session.add(shot)
    await session.commit()
    await session.refresh(shot)

    # Opportunistically purge anything past its retention window.
    await delete_expired(session)
    return ScreenshotOut.model_validate(shot)


@router.post("/location", status_code=status.HTTP_204_NO_CONTENT)
async def report_location(
    payload: LocationReportIn, session: SessionDep, device: CurrentDevice
):
    """Record a location result from the device.

    A coordinate is stored only when the device actually obtained a fix
    (status == "ok"). An "unavailable" or "permission_restricted" result clears
    any pending request but is never stored as coordinates - we do not invent a
    location.
    """
    policy = await session.scalar(
        select(LocationPolicy).where(LocationPolicy.device_id == device.id)
    )
    retention_days = policy.retention_days if policy else 30
    if policy is not None and policy.requested_at is not None:
        policy.requested_at = None

    if (
        payload.status == "ok"
        and payload.latitude is not None
        and payload.longitude is not None
    ):
        now = datetime.now(timezone.utc)
        session.add(
            LocationPoint(
                device_id=device.id,
                captured_at=now,
                latitude=payload.latitude,
                longitude=payload.longitude,
                accuracy_m=payload.accuracy_m,
                source=(payload.source or "windows_agent")[:32],
                retention_until=now + timedelta(days=retention_days),
            )
        )
    await session.commit()
