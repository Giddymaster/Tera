"""HTTP client for the management backend.

Network calls that may fail transiently (heartbeat, usage) return False instead
of raising, so the caller can queue and retry. Enrollment raises on failure
because it is a one-time setup step.
"""

from __future__ import annotations

import httpx

from . import AGENT_VERSION


class EnrollError(Exception):
    pass


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(timeout=timeout)

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def enroll(self, device_uid: str, enrollment_secret: str) -> str:
        try:
            resp = self._http.post(
                f"{self.base_url}/agent/enroll",
                json={"device_uid": device_uid, "enrollment_secret": enrollment_secret},
            )
        except httpx.HTTPError as exc:
            raise EnrollError(f"Could not reach server: {exc}") from exc
        if resp.status_code != 200:
            raise EnrollError(f"Enrollment rejected ({resp.status_code}).")
        return resp.json()["device_token"]

    def heartbeat(self, token: str, health: dict) -> bool:
        payload = {"agent_version": AGENT_VERSION, **health}
        try:
            resp = self._http.post(
                f"{self.base_url}/agent/heartbeat",
                json=payload,
                headers=self._auth(token),
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def report_usage(self, token: str, entries: list[dict]) -> bool:
        if not entries:
            return True
        try:
            resp = self._http.post(
                f"{self.base_url}/agent/usage",
                json={"entries": entries},
                headers=self._auth(token),
            )
            return resp.status_code in (200, 204)
        except httpx.HTTPError:
            return False

    def close(self) -> None:
        self._http.close()
