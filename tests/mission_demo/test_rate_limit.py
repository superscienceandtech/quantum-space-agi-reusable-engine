from __future__ import annotations

import pytest

from quantum_space_agi.mission_demo.rate_limit import (
    MAX_RATE_LIMIT_ENTRIES,
    FixedWindowRateLimiter,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def limiter(clock: FakeClock) -> FixedWindowRateLimiter:
    return FixedWindowRateLimiter(clock=clock)


def test_allows_requests_through_exact_limit_boundary(
    limiter: FixedWindowRateLimiter,
) -> None:
    assert limiter.check("user-a", "run", limit=2) is None
    assert limiter.check("user-a", "run", limit=2) is None


def test_blocks_first_request_over_limit_with_positive_retry_delay(
    limiter: FixedWindowRateLimiter,
) -> None:
    limiter.check("user-a", "run", limit=1)

    retry_after = limiter.check("user-a", "run", limit=1)

    assert retry_after is not None
    assert retry_after > 0


def test_isolates_users_and_route_keys(limiter: FixedWindowRateLimiter) -> None:
    limiter.check("user-a", "run", limit=1)

    assert limiter.check("user-b", "run", limit=1) is None
    assert limiter.check("user-a", "validate", limit=1) is None


def test_recovers_at_next_fixed_window(
    limiter: FixedWindowRateLimiter, clock: FakeClock
) -> None:
    assert limiter.check("user-a", "run", limit=1) is None
    assert limiter.check("user-a", "run", limit=1) == 60

    clock.now = 60.0

    assert limiter.check("user-a", "run", limit=1) is None


def test_bounds_entries_and_recovers_after_the_active_window(
    limiter: FixedWindowRateLimiter, clock: FakeClock
) -> None:
    for user_number in range(MAX_RATE_LIMIT_ENTRIES):
        assert limiter.check(f"user-{user_number}", "run", limit=1) is None

    retry_after = limiter.check("overflow-user", "run", limit=1)
    assert retry_after is not None
    assert retry_after > 0

    clock.now = 60.0

    assert limiter.check("overflow-user", "run", limit=1) is None


def test_uses_injected_clock_when_explicit_time_is_not_supplied(
    clock: FakeClock,
) -> None:
    limiter = FixedWindowRateLimiter(clock=clock)
    clock.now = 12.5

    retry_after = limiter.check("user-a", "run", limit=1)

    assert retry_after is None
    assert limiter.check("user-a", "run", limit=1) == 48
