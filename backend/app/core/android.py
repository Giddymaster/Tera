"""Android Management API (AMAPI) integration.

This activates only when ``ANDROID_PROJECT_ID``, ``ANDROID_ENTERPRISE_NAME``, and
``ANDROID_SA_JSON`` are all configured (see docs/android-feasibility.md). Until
then every live method raises :class:`AndroidNotConfigured`, and the API returns
a clear "not configured" response.

IMPORTANT: the live AMAPI calls below are written from Google's documented REST
API but have NOT been exercised against a real enterprise and device in this
project. They need a Google Cloud project, a service account, an enterprise
binding, and a physical Android device to verify. Treat them as an integration
scaffold until that verification is done.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from app.core.config import get_settings

_SCOPE = "https://www.googleapis.com/auth/androidmanagement"
_BASE = "https://androidmanagement.googleapis.com/v1"

# The device commands AMAPI supports (verified against the issueCommand docs).
VALID_COMMANDS = {
    "LOCK",
    "RESET_PASSWORD",
    "REBOOT",
    "RELINQUISH_OWNERSHIP",
    "CLEAR_APP_DATA",
    "START_LOST_MODE",
    "STOP_LOST_MODE",
    "WIPE",
    "REQUEST_DEVICE_INFO",
}

# What the dashboard advertises as available on Android via AMAPI.
CAPABILITIES = {
    "inventory": True,
    "compliance": True,
    "managed_apps": True,
    "remote_lock": True,
    "remote_wipe": True,
    "reboot": True,
    "location": "lost_mode_only",  # no continuous GPS; via Lost Mode only
    "screenshots": False,
    "live_screen_view": False,
    "app_usage": False,
}


class AndroidNotConfigured(Exception):
    pass


class AndroidApiError(Exception):
    pass


@dataclass
class AndroidConfig:
    project_id: str
    enterprise_name: str
    sa_json: str


def get_android_config() -> AndroidConfig | None:
    s = get_settings()
    if s.android_project_id and s.android_enterprise_name and s.android_sa_json:
        return AndroidConfig(
            project_id=s.android_project_id,
            enterprise_name=s.android_enterprise_name,
            sa_json=s.android_sa_json,
        )
    return None


def is_configured() -> bool:
    return get_android_config() is not None


def _load_service_account_info(sa_json: str) -> dict:
    """Accept either a path to a JSON key file or inline JSON."""
    candidate = sa_json.strip()
    if candidate.startswith("{"):
        return json.loads(candidate)
    return json.loads(Path(candidate).read_text(encoding="utf-8"))


class AndroidClient:
    def __init__(self, config: AndroidConfig) -> None:
        self.config = config
        # Imported lazily so the dependency is only needed when configured.
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account

        info = _load_service_account_info(config.sa_json)
        self._creds = service_account.Credentials.from_service_account_info(
            info, scopes=[_SCOPE]
        )
        self._request = Request()

    def _headers(self) -> dict[str, str]:
        if not self._creds.valid:
            self._creds.refresh(self._request)
        return {"Authorization": f"Bearer {self._creds.token}"}

    def _get(self, url: str) -> dict[str, Any]:
        try:
            resp = httpx.get(url, headers=self._headers(), timeout=20.0)
        except httpx.HTTPError as exc:
            raise AndroidApiError(str(exc)) from exc
        if resp.status_code >= 400:
            raise AndroidApiError(f"{resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def _post(self, url: str, body: dict) -> dict[str, Any]:
        try:
            resp = httpx.post(url, headers=self._headers(), json=body, timeout=20.0)
        except httpx.HTTPError as exc:
            raise AndroidApiError(str(exc)) from exc
        if resp.status_code >= 400:
            raise AndroidApiError(f"{resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def list_devices(self) -> list[dict]:
        data = self._get(f"{_BASE}/{self.config.enterprise_name}/devices")
        return data.get("devices", [])

    def get_device(self, device_name: str) -> dict:
        return self._get(f"{_BASE}/{device_name}")

    def create_enrollment_token(self, policy_name: str = "default") -> dict:
        body = {
            "policyName": f"{self.config.enterprise_name}/policies/{policy_name}",
            "duration": "3600s",
        }
        return self._post(
            f"{_BASE}/{self.config.enterprise_name}/enrollmentTokens", body
        )

    def issue_command(self, device_name: str, command_type: str) -> dict:
        if command_type not in VALID_COMMANDS:
            raise AndroidApiError(f"Unsupported command: {command_type}")
        return self._post(f"{_BASE}/{device_name}:issueCommand", {"type": command_type})


def get_client() -> AndroidClient:
    config = get_android_config()
    if config is None:
        raise AndroidNotConfigured(
            "Android management is not configured. Set ANDROID_PROJECT_ID, "
            "ANDROID_ENTERPRISE_NAME, and ANDROID_SA_JSON. See "
            "docs/android-feasibility.md."
        )
    return AndroidClient(config)
