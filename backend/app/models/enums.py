"""Enumerations shared across models and schemas."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """Administrator roles. Permissions are derived from these."""

    OWNER = "owner"       # full control, including managing admins and policy
    ADMIN = "admin"       # day-to-day device management and monitoring
    VIEWER = "viewer"     # read-only: devices and reports


class Permission(str, Enum):
    """Granular permissions checked by endpoints (least-privilege)."""

    VIEW_DEVICES = "view_devices"
    MANAGE_DEVICES = "manage_devices"
    VIEW_REPORTS = "view_reports"
    VIEW_SCREENSHOTS = "view_screenshots"
    INITIATE_LIVE_SESSION = "initiate_live_session"
    MANAGE_SECURITY_POLICY = "manage_security_policy"
    MANAGE_ADMINS = "manage_admins"


# Which permissions each role grants. Endpoints check a permission, never a
# role directly, so permissions can be re-mapped without touching endpoints.
ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.OWNER: frozenset(Permission),
    Role.ADMIN: frozenset(
        {
            Permission.VIEW_DEVICES,
            Permission.MANAGE_DEVICES,
            Permission.VIEW_REPORTS,
            Permission.VIEW_SCREENSHOTS,
            Permission.INITIATE_LIVE_SESSION,
        }
    ),
    Role.VIEWER: frozenset(
        {
            Permission.VIEW_DEVICES,
            Permission.VIEW_REPORTS,
        }
    ),
}


def permissions_for(role: Role) -> frozenset[Permission]:
    return ROLE_PERMISSIONS.get(role, frozenset())


class OSType(str, Enum):
    WINDOWS = "windows"
    ANDROID = "android"
    IOS = "ios"


class DeviceType(str, Enum):
    LAPTOP = "laptop"
    PHONE = "phone"
    TABLET = "tablet"


class EnrollmentStatus(str, Enum):
    PENDING = "pending"     # created, awaiting first agent check-in
    ENROLLED = "enrolled"   # agent has authenticated at least once
    REVOKED = "revoked"     # access revoked; device may not submit data
