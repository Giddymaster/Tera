"""Fleet alerts and summary reporting."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import SessionDep, require_permission
from app.core.alerts import OFFLINE_SECONDS, compute_device_alerts, severity_rank
from app.core.config import get_settings
from app.models.admin import Admin
from app.models.device import Device
from app.models.enums import EnrollmentStatus, Permission
from app.models.monitoring import RemoteSession, Screenshot
from app.schemas.reports import AlertOut, ReportSummaryOut

settings = get_settings()
router = APIRouter(tags=["reports"])

ViewDevices = Annotated[Admin, Depends(require_permission(Permission.VIEW_DEVICES))]
ViewReports = Annotated[Admin, Depends(require_permission(Permission.VIEW_REPORTS))]


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(session: SessionDep, admin: ViewDevices):
    now = datetime.now(timezone.utc)
    devices = (await session.execute(select(Device))).scalars().all()
    alerts: list[dict] = []
    for device in devices:
        alerts.extend(compute_device_alerts(device, now))
    alerts.sort(key=lambda a: (severity_rank(a["severity"]), a["device_name"]))
    return alerts


@router.get("/reports/summary", response_model=ReportSummaryOut)
async def report_summary(session: SessionDep, admin: ViewReports):
    now = datetime.now(timezone.utc)
    devices = (await session.execute(select(Device))).scalars().all()

    online = offline = pending = revoked = updates = 0
    by_os: dict[str, int] = {}
    alerts_total = alerts_warning = 0

    for d in devices:
        by_os[d.os_type.value] = by_os.get(d.os_type.value, 0) + 1
        if d.enrollment_status == EnrollmentStatus.REVOKED:
            revoked += 1
        elif d.enrollment_status == EnrollmentStatus.PENDING:
            pending += 1
        else:
            last = _aware(d.last_seen_at)
            if last is not None and (now - last).total_seconds() <= OFFLINE_SECONDS:
                online += 1
            else:
                offline += 1
        if d.agent_version and d.agent_version != settings.agent_latest_version:
            updates += 1
        for a in compute_device_alerts(d, now):
            alerts_total += 1
            if a["severity"] == "warning":
                alerts_warning += 1

    active_sessions = await session.scalar(
        select(func.count())
        .select_from(RemoteSession)
        .where(RemoteSession.status == "active")
    )
    screenshots_total = await session.scalar(
        select(func.count()).select_from(Screenshot)
    )

    return ReportSummaryOut(
        total_devices=len(devices),
        online=online,
        offline=offline,
        pending=pending,
        revoked=revoked,
        by_os=by_os,
        alerts_total=alerts_total,
        alerts_warning=alerts_warning,
        active_sessions=int(active_sessions or 0),
        screenshots_total=int(screenshots_total or 0),
        updates_available=updates,
    )
