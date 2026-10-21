"""HTTP client for the management backend.

Network calls that may fail transiently (heartbeat, usage) return False instead
of raising, so the caller can queue and retry. Enrollment raises on failure
because it is a one-time setup step.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from . import AGENT_VERSION


class EnrollError(Exception):
    pass


@dataclass
class HeartbeatResult:
    ok: bool
    status: int  # HTTP status, or 0 if the request never completed
    update_available: bool = False
    latest_version: str | None = None

    @property
    def revoked(self) -> bool:
        # A previously valid device token being rejected means access was revoked.
        return self.status == 401


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

    def heartbeat(self, token: str, health: dict) -> HeartbeatResult:
        payload = {"agent_version": AGENT_VERSION, **health}
        try:
            resp = self._http.post(
                f"{self.base_url}/agent/heartbeat",
                json=payload,
                headers=self._auth(token),
            )
        except httpx.HTTPError:
            return HeartbeatResult(ok=False, status=0)
        if resp.status_code != 200:
            return HeartbeatResult(ok=False, status=resp.status_code)
        data = resp.json()
        return HeartbeatResult(
            ok=True,
            status=200,
            update_available=bool(data.get("update_available")),
            latest_version=data.get("latest_agent_version"),
        )

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

    def get_directives(self, token: str) -> dict | None:
        try:
            resp = self._http.get(
                f"{self.base_url}/agent/directives", headers=self._auth(token)
            )
        except httpx.HTTPError:
            return None
        if resp.status_code != 200:
            return None
        return resp.json()

    def upload_screenshot(
        self,
        token: str,
        image_base64: str,
        trigger: str,
        foreground_app: str | None,
        session_id: int | None,
        width: int,
        height: int,
    ) -> bool:
        try:
            resp = self._http.post(
                f"{self.base_url}/agent/screenshot",
                json={
                    "image_base64": image_base64,
                    "trigger": trigger,
                    "foreground_app": foreground_app,
                    "session_id": session_id,
                    "width": width,
                    "height": height,
                },
                headers=self._auth(token),
                timeout=30.0,
            )
            return resp.status_code in (200, 201)
        except httpx.HTTPError:
            return False

    def report_location(self, token: str, payload: dict) -> bool:
        try:
            resp = self._http.post(
                f"{self.base_url}/agent/location",
                json=payload,
                headers=self._auth(token),
            )
            return resp.status_code in (200, 204)
        except httpx.HTTPError:
            return False

    def close(self) -> None:
        self._http.close()
