"""Best-effort RustDesk setup for unattended remote control.

When the server enables RustDesk (directives.rustdesk), the agent downloads the
RustDesk client, points it at the self-hosted server, sets an unattended
password, starts it, reads its ID, and reports the ID + password to the backend.

IMPORTANT: this is best-effort and NOT tested end-to-end in this project.
RustDesk's CLI flags and config format vary by version. Each step is wrapped so a
failure only logs and returns None (the agent keeps running). True pre-login
unattended access also needs RustDesk installed as a service, which requires
administrator rights (a one-time manual step: run `rustdesk.exe --install-service`
elevated). Without that, remote control works while a user is signed in.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import subprocess
import time
import urllib.request
from pathlib import Path

log = logging.getLogger("agent.rustdesk")

_CREATE_NO_WINDOW = 0x08000000
_API_LATEST = "https://api.github.com/repos/rustdesk/rustdesk/releases/latest"


def _exe_path(install_dir: Path) -> Path:
    return install_dir / "rustdesk.exe"


def _latest_exe_url() -> str | None:
    try:
        req = urllib.request.Request(_API_LATEST, headers={"User-Agent": "tera-agent"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
    except Exception:  # noqa: BLE001
        return None
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.endswith("x86_64.exe"):
            return asset.get("browser_download_url")
    return None


def _ensure_installed(install_dir: Path) -> Path | None:
    exe = _exe_path(install_dir)
    if exe.exists():
        return exe
    url = _latest_exe_url()
    if not url:
        log.warning("Could not find a RustDesk download URL.")
        return None
    try:
        log.info("Downloading RustDesk...")
        urllib.request.urlretrieve(url, exe)  # noqa: S310 - trusted GitHub release
        return exe
    except Exception:  # noqa: BLE001
        log.exception("RustDesk download failed.")
        return None


def _write_config(host: str, key: str) -> None:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return
    cfg_dir = Path(appdata) / "RustDesk" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    toml = (
        f"rendezvous_server = '{host}'\n"
        "nat_type = 1\n"
        "serial = 0\n\n"
        "[options]\n"
        f"custom-rendezvous-server = '{host}'\n"
        f"relay-server = '{host}'\n"
        "api-server = ''\n"
        f"key = '{key}'\n"
    )
    (cfg_dir / "RustDesk2.toml").write_text(toml, encoding="utf-8")


def _run(exe: Path, *args: str, timeout: int = 40) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            [str(exe), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=_CREATE_NO_WINDOW,
        )
    except Exception:  # noqa: BLE001
        return None


def setup(install_dir: str | Path, host: str, key: str) -> tuple[str, str] | None:
    """Configure RustDesk and return (rustdesk_id, password), or None on failure."""
    install_dir = Path(install_dir)
    exe = _ensure_installed(install_dir)
    if exe is None:
        return None

    try:
        _write_config(host, key)
    except Exception:  # noqa: BLE001
        log.exception("Writing RustDesk config failed; continuing.")

    password = secrets.token_urlsafe(9)
    _run(exe, "--password", password)

    # Launch RustDesk so it registers with the server and is connectable.
    try:
        subprocess.Popen([str(exe)], creationflags=_CREATE_NO_WINDOW)
    except Exception:  # noqa: BLE001
        log.exception("Launching RustDesk failed.")
    time.sleep(4)

    result = _run(exe, "--get-id")
    rustdesk_id = (result.stdout.strip() if result and result.stdout else "")
    if not rustdesk_id:
        log.warning("Could not read the RustDesk ID yet.")
        return None
    return rustdesk_id, password
