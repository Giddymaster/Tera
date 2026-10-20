"""Keep the agent running: restart it with backoff if it exits unexpectedly.

The agent itself already handles network outages and per-cycle errors. This
supervisor is the outer safety net for the rare case where the agent process
exits or crashes, so a managed device keeps reporting without manual action.

It does NOT restart on a clean stop (Ctrl+C) or when the device has been revoked.
"""

from __future__ import annotations

import logging
import time

from .runner import run

log = logging.getLogger("agent.supervisor")


def supervise(
    config_path: str,
    base_delay: float = 5.0,
    max_delay: float = 60.0,
    stable_after: float = 120.0,
) -> int:
    delay = base_delay
    while True:
        start = time.monotonic()
        try:
            code = run(config_path)
        except KeyboardInterrupt:
            log.info("Supervisor stopping (interrupted).")
            return 0
        except Exception:  # noqa: BLE001 - last-resort guard; log and restart
            log.exception("Agent crashed with an unhandled error.")
            code = 1

        if code == 0:
            return 0  # clean stop requested
        if code == 2:
            log.info("Agent stopped because access was revoked; supervisor exiting.")
            return 2

        # If the agent ran for a decent while before exiting, reset the backoff.
        if time.monotonic() - start >= stable_after:
            delay = base_delay

        log.warning("Agent exited (code %s); restarting in %.0fs.", code, delay)
        try:
            time.sleep(delay)
        except KeyboardInterrupt:
            return 0
        delay = min(max_delay, delay * 2)
