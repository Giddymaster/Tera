"""A small in-memory rate limiter for sensitive endpoints (e.g. login).

This is intentionally simple: a sliding window kept in process memory, keyed by
client IP. It is enough for a single-process deployment serving a handful of
admins. If the backend is ever scaled to multiple processes or machines, this
should be replaced with a shared store (e.g. Redis), because each process would
otherwise keep its own separate counts.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> None:
        window_start = now - self.window_seconds
        hits = self._hits[key]
        while hits and hits[0] < window_start:
            hits.popleft()

    def is_allowed(self, key: str) -> bool:
        """Record an attempt and return True if it is within the limit."""
        now = time.monotonic()
        with self._lock:
            self._prune(key, now)
            hits = self._hits[key]
            if len(hits) >= self.max_attempts:
                return False
            hits.append(now)
            return True

    def retry_after(self, key: str) -> int:
        """Seconds until the oldest recorded hit leaves the window."""
        now = time.monotonic()
        with self._lock:
            self._prune(key, now)
            hits = self._hits[key]
            if not hits:
                return 0
            return max(0, int(self.window_seconds - (now - hits[0])) + 1)

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._hits.clear()
            else:
                self._hits.pop(key, None)
