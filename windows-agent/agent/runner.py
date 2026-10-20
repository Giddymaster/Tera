"""Main agent loop: enroll, then sample foreground usage and report in.

Reliability:
- usage entries that fail to send are queued to disk and retried next cycle;
- heartbeats are best-effort and simply retried on the next interval;
- all network failures are caught so the agent keeps running through outages.
"""

from __future__ import annotations

import base64
import logging
import time
from datetime import datetime
from pathlib import Path

from . import AGENT_VERSION
from .capture import capture_jpeg
from .client import ApiClient, EnrollError
from .config import load_config
from .foreground import foreground_process_name, idle_seconds
from .health import collect_health
from .state import StateStore
from .tracker import UsageTracker, merge_entries

log = logging.getLogger("agent")

NOTICE = (
    "\n"
    "============================================================\n"
    " Employee Device Manager - monitoring agent\n"
    " This company-owned device is managed. The agent reports\n"
    " device health and the NAMES of foreground applications and\n"
    " how long they are used. It does NOT record keystrokes,\n"
    " clipboard, window titles, URLs, or screen contents.\n"
    "============================================================\n"
)


def _state_path(config_path: str) -> Path:
    return Path(config_path).resolve().parent / ".agent_state.json"


def _within_active_hours(start: int | None, end: int | None) -> bool:
    """True if the current local hour is within [start, end). None = always."""
    if start is None or end is None:
        return True
    hour = datetime.now().hour
    if start == end:
        return True
    if start < end:
        return start <= hour < end
    # Window wraps past midnight (e.g. 22 -> 6).
    return hour >= start or hour < end


def run(config_path: str = "config.json") -> int:
    cfg = load_config(config_path)
    state = StateStore(_state_path(config_path))
    client = ApiClient(cfg.base_url)

    print(NOTICE)
    log.info("Agent %s starting; server=%s", AGENT_VERSION, cfg.base_url)

    # Enroll once; reuse the stored device token afterwards.
    token = state.device_token
    if not token:
        try:
            token = client.enroll(cfg.device_uid, cfg.enrollment_secret)
        except EnrollError as exc:
            log.error("Enrollment failed: %s", exc)
            return 1
        state.set_device_token(token)
        log.info("Enrolled successfully; device token stored.")
    else:
        log.info("Using stored device token.")

    tracker = UsageTracker()
    pending = state.load_pending_usage()

    interval = cfg.sample_interval_seconds
    last_heartbeat = 0.0
    last_flush = time.monotonic()

    # Screenshot / session state.
    directives: dict = {}
    last_directives_poll = 0.0
    last_scheduled_capture = 0.0
    last_session_capture = 0.0

    def do_capture(trigger: str, session_id: int | None = None) -> None:
        shot = capture_jpeg()
        if shot is None:
            log.info("Screenshot capture unavailable on this session.")
            return
        data, width, height = shot
        b64 = base64.b64encode(data).decode()
        ok = client.upload_screenshot(
            token, b64, trigger, foreground_process_name(), session_id, width, height
        )
        log.info("Screenshot (%s) %s", trigger, "uploaded" if ok else "failed")

    def flush_usage() -> None:
        nonlocal pending
        combined = merge_entries(pending + tracker.drain())
        if not combined:
            return
        if client.report_usage(token, combined):
            pending = []
            log.info("Reported usage for %d app(s).", len(combined))
        else:
            pending = combined
            log.warning("Usage report failed; queued %d app(s) for retry.", len(combined))
        state.save_pending_usage(pending)

    update_notified = False

    def do_heartbeat() -> bool:
        """Send a heartbeat. Returns False if the device has been revoked."""
        nonlocal update_notified
        result = client.heartbeat(token, collect_health())
        if result.revoked:
            log.warning("Access revoked by the server; the agent will stop.")
            return False
        if not result.ok:
            log.info("Heartbeat failed (will retry next cycle).")
            return True
        if result.update_available and not update_notified:
            log.warning(
                "A newer agent version (%s) is available; this agent is %s. "
                "An administrator can update it.",
                result.latest_version,
                AGENT_VERSION,
            )
            update_notified = True
        return True

    try:
        # Immediate first heartbeat so the device shows online quickly.
        if not do_heartbeat():
            return 2  # revoked -> do not let the supervisor restart us
        last_heartbeat = time.monotonic()

        while True:
            time.sleep(interval)
            try:
                tracker.sample(interval, foreground_process_name(), idle_seconds())
                now = time.monotonic()
                if now - last_heartbeat >= cfg.heartbeat_interval_seconds:
                    if not do_heartbeat():
                        return 2
                    last_heartbeat = now
                if now - last_flush >= cfg.usage_flush_interval_seconds:
                    flush_usage()
                    last_flush = now

                # Refresh directives (policy, capture requests, active session).
                if not directives or now - last_directives_poll >= 15:
                    fresh = client.get_directives(token)
                    if fresh is not None:
                        directives = fresh
                    last_directives_poll = now

                policy = directives.get("screenshot_policy") or {}
                fg = foreground_process_name()
                excluded = {a.lower() for a in policy.get("excluded_apps", [])}
                fg_excluded = bool(fg and fg.lower() in excluded)

                # On-demand capture requested by an admin.
                if directives.get("capture_requested") and not fg_excluded:
                    do_capture("request")
                    directives["capture_requested"] = False
                    last_directives_poll = now - 12  # re-check soon

                # Scheduled capture per policy.
                if policy.get("enabled") and not fg_excluded:
                    interval_s = max(1, int(policy.get("interval_minutes", 15))) * 60
                    if now - last_scheduled_capture >= interval_s and _within_active_hours(
                        policy.get("active_hour_start"), policy.get("active_hour_end")
                    ):
                        do_capture("schedule")
                        last_scheduled_capture = now

                # Active live-support session: near-live snapshots + consent notice.
                if directives.get("session_active"):
                    sid = directives.get("session_id")
                    sci = directives.get("session_capture_interval_seconds", 4)
                    if now - last_session_capture >= sci:
                        log.warning(
                            "LIVE SUPPORT SESSION ACTIVE (id=%s): your screen is being "
                            "viewed by an administrator.",
                            sid,
                        )
                        if not fg_excluded:
                            do_capture("session", sid)
                        last_session_capture = now
            except Exception:  # noqa: BLE001 - keep running through transient errors
                log.exception("Error during agent cycle; continuing.")
    except KeyboardInterrupt:
        log.info("Stopping; flushing remaining usage...")
        flush_usage()
    finally:
        client.close()
    return 0
