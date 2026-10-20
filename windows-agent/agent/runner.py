"""Main agent loop: enroll, then sample foreground usage and report in.

Reliability:
- usage entries that fail to send are queued to disk and retried next cycle;
- heartbeats are best-effort and simply retried on the next interval;
- all network failures are caught so the agent keeps running through outages.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from . import AGENT_VERSION
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

    try:
        # Send an immediate first heartbeat so the device shows online quickly.
        if client.heartbeat(token, collect_health()):
            log.info("Initial heartbeat sent.")
        last_heartbeat = time.monotonic()

        while True:
            time.sleep(interval)
            tracker.sample(interval, foreground_process_name(), idle_seconds())

            now = time.monotonic()
            if now - last_heartbeat >= cfg.heartbeat_interval_seconds:
                ok = client.heartbeat(token, collect_health())
                log.info("Heartbeat %s", "ok" if ok else "failed (will retry)")
                last_heartbeat = now
            if now - last_flush >= cfg.usage_flush_interval_seconds:
                flush_usage()
                last_flush = now
    except KeyboardInterrupt:
        log.info("Stopping; flushing remaining usage...")
        flush_usage()
    finally:
        client.close()
    return 0
