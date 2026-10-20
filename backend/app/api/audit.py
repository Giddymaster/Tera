"""Admin-facing audit log viewing."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.deps import SessionDep, require_permission
from app.models.admin import Admin
from app.models.audit import AuditLog
from app.models.enums import Permission
from app.schemas.audit import AuditLogOut

router = APIRouter(prefix="/audit", tags=["audit"])

ViewReports = Annotated[Admin, Depends(require_permission(Permission.VIEW_REPORTS))]


@router.get("", response_model=list[AuditLogOut])
async def list_audit_logs(
    session: SessionDep,
    admin: ViewReports,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    result = await session.execute(
        select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all())
