"""Accumulate foreground application usage in seconds, per app name.

Time while the user is idle (no keyboard/mouse for a threshold) is not counted,
so usage reflects active work rather than a screen left open.
"""

from __future__ import annotations


class UsageTracker:
    def __init__(self, idle_threshold_seconds: float = 180.0) -> None:
        self.idle_threshold = idle_threshold_seconds
        self._counts: dict[str, int] = {}

    def sample(self, seconds: int, app_name: str | None, idle_seconds: float) -> None:
        if not app_name or idle_seconds >= self.idle_threshold:
            return
        self._counts[app_name] = self._counts.get(app_name, 0) + seconds

    def drain(self) -> list[dict]:
        """Return accumulated entries and reset the counters."""
        entries = [
            {"app_name": name, "seconds": secs}
            for name, secs in self._counts.items()
            if secs > 0
        ]
        self._counts = {}
        return entries


def merge_entries(entries: list[dict]) -> list[dict]:
    """Sum durations for repeated app names and drop zero/negative values."""
    agg: dict[str, int] = {}
    for e in entries:
        name = e.get("app_name")
        secs = int(e.get("seconds", 0))
        if not name or secs <= 0:
            continue
        agg[name] = agg.get(name, 0) + secs
    return [{"app_name": n, "seconds": s} for n, s in agg.items()]
