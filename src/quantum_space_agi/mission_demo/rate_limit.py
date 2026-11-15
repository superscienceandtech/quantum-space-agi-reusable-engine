"""Bounded process-local fixed-window rate limiting for mission operations."""

from __future__ import annotations

import math
import threading
import time
from collections import OrderedDict
from collections.abc import Callable

MAX_RATE_LIMIT_ENTRIES = 10_000
_WINDOW_SECONDS = 60.0


class FixedWindowRateLimiter:
    """Track request counts per user and route for one-minute windows."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._entries: OrderedDict[tuple[str, str], tuple[int, int]] = OrderedDict()

    def check(
        self,
        user_id: str,
        route_key: str,
        limit: int,
        now: float | None = None,
    ) -> int | None:
        if not user_id or not route_key:
            raise ValueError("user_id and route_key must not be empty")
        if limit < 1:
            raise ValueError("limit must be positive")

        current_time = self._clock() if now is None else now
        if not math.isfinite(current_time):
            raise ValueError("current time must be finite")
        current_window = math.floor(current_time / _WINDOW_SECONDS)
        key = (user_id, route_key)

        with self._lock:
            while self._entries:
                first_key = next(iter(self._entries))
                first_window, _ = self._entries[first_key]
                if first_window >= current_window:
                    break
                self._entries.popitem(last=False)

            existing = self._entries.get(key)
            if existing is not None and existing[0] == current_window:
                if existing[1] >= limit:
                    return self._retry_after(current_time, current_window)
                self._entries[key] = (current_window, existing[1] + 1)
                return None

            if len(self._entries) >= MAX_RATE_LIMIT_ENTRIES:
                return self._retry_after(current_time, current_window)

            self._entries[key] = (current_window, 1)
            return None

    @staticmethod
    def _retry_after(current_time: float, current_window: int) -> int:
        window_end = (current_window + 1) * _WINDOW_SECONDS
        return max(1, math.ceil(window_end - current_time))
