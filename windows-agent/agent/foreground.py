"""Detect the foreground application's name on Windows.

Returns the executable/process name only (e.g. "chrome.exe"). It deliberately
does NOT read the window title, which can contain document names, URLs, or other
sensitive content.

Also reports user idle time so the tracker can avoid counting time when the user
is away from the keyboard and mouse.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]


def foreground_process_name() -> str | None:
    """The process name of the window currently in focus, or None."""
    try:
        user32 = ctypes.windll.user32
    except AttributeError:
        return None  # not on Windows

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return None

    if psutil is not None:
        try:
            return psutil.Process(pid.value).name()
        except Exception:  # noqa: BLE001 - process may have exited
            return None
    return None


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def idle_seconds() -> float:
    """Seconds since the last keyboard/mouse input (0.0 if unavailable)."""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
    except AttributeError:
        return 0.0
    info = _LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(info)
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0
    millis = kernel32.GetTickCount() - info.dwTime
    return max(0.0, millis / 1000.0)
