"""Agent configuration loaded from a JSON file."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_DEFAULTS = {
    "heartbeat_interval_seconds": 60,
    "usage_flush_interval_seconds": 120,
    "sample_interval_seconds": 5,
}


@dataclass
class Config:
    server_url: str
    device_uid: str
    enrollment_secret: str
    heartbeat_interval_seconds: int = 60
    usage_flush_interval_seconds: int = 120
    sample_interval_seconds: int = 5

    @property
    def base_url(self) -> str:
        return self.server_url.rstrip("/")


def load_config(path: str | Path) -> Config:
    path = Path(path)
    # utf-8-sig tolerates a UTF-8 BOM (which Windows PowerShell / Notepad may add)
    # and reads plain UTF-8 fine.
    with path.open(encoding="utf-8-sig") as f:
        data = json.load(f)

    required = ("server_url", "device_uid", "enrollment_secret")
    missing = [k for k in required if not data.get(k)]
    if missing:
        raise ValueError(
            f"Config {path} is missing required keys: {', '.join(missing)}"
        )

    merged = {**_DEFAULTS, **{k: data[k] for k in data if k in Config.__annotations__}}
    return Config(**merged)
