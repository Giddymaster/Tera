"""Apple MDM (iPhone/iPad) configuration and capability reporting.

Unlike Android (a REST API), a live Apple MDM requires running an MDM server that
speaks the MDM protocol over APNs with signed profiles, plus an APNs vendor
certificate, Apple Business Manager, and a device. That server is NOT implemented
here (see docs/apple-mdm-feasibility.md). This module provides configuration
detection and the honest capability matrix the dashboard shows.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings

# What standard Apple MDM can do, with honest limits.
CAPABILITIES = {
    "inventory": True,
    "os_security_info": True,
    "managed_apps": True,
    "config_profiles": True,
    "remote_lock": True,
    "remote_wipe": True,
    "lost_mode": "supervised_only",
    "location": "lost_mode_supervised_only",
    "screenshots": False,
    "live_screen_view": False,
    "app_usage": False,
}

# Enrollment models, most to least capable.
ENROLLMENT_MODELS = [
    {"name": "Automated Device Enrollment (ABM)", "supervised": True,
     "note": "Company-owned via Apple/reseller; most capable"},
    {"name": "Apple Configurator", "supervised": True,
     "note": "Manually supervise company-owned devices via USB"},
    {"name": "Device Enrollment (profile)", "supervised": False,
     "note": "Install a profile manually; fewer capabilities"},
    {"name": "User Enrollment (BYOD)", "supervised": False,
     "note": "Personal devices; most limited; no Lost Mode"},
]


@dataclass
class AppleConfig:
    server_url: str
    push_topic: str


def get_apple_config() -> AppleConfig | None:
    s = get_settings()
    if s.apple_mdm_server_url:
        return AppleConfig(
            server_url=s.apple_mdm_server_url,
            push_topic=s.apple_mdm_push_topic,
        )
    return None


def is_configured() -> bool:
    return get_apple_config() is not None
