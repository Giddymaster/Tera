"""Persistent agent state: the device token and any queued usage entries.

The device token authenticates the agent to the backend, so the state file is a
secret. It is written next to the config by default and must never be committed
to version control.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock


class StateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = Lock()
        self._data: dict = {"device_token": None, "pending_usage": []}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        self._data.setdefault("device_token", None)
        self._data.setdefault("pending_usage", [])

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data), encoding="utf-8")
        tmp.replace(self.path)

    @property
    def device_token(self) -> str | None:
        return self._data.get("device_token")

    def set_device_token(self, token: str) -> None:
        with self._lock:
            self._data["device_token"] = token
            self._save()

    def load_pending_usage(self) -> list[dict]:
        return list(self._data.get("pending_usage", []))

    def save_pending_usage(self, entries: list[dict]) -> None:
        with self._lock:
            self._data["pending_usage"] = entries
            self._save()
