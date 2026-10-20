"""Collect supported device-health metrics.

Only non-sensitive, work-relevant health data: OS version, free/total disk space
on the system drive, and battery/power status. No personal files are read.
"""

from __future__ import annotations

import os
import platform
import shutil

try:
    import psutil
except ImportError:  # psutil is optional; health degrades gracefully without it.
    psutil = None  # type: ignore[assignment]

_GB = 1_000_000_000


def collect_health() -> dict:
    health: dict = {"os_version": platform.platform()}

    system_drive = os.environ.get("SystemDrive", "C:") + "\\"
    try:
        total, _used, free = shutil.disk_usage(system_drive)
        health["disk_total_gb"] = round(total / _GB, 2)
        health["disk_free_gb"] = round(free / _GB, 2)
    except OSError:
        pass

    if psutil is not None:
        try:
            battery = psutil.sensors_battery()
        except Exception:  # noqa: BLE001 - platform quirks; health is best-effort
            battery = None
        if battery is not None:
            health["battery_percent"] = int(battery.percent)
            health["power_plugged"] = bool(battery.power_plugged)

    return health
