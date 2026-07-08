"""
Unit tests for the Circuit Breaker.

Run with:

    pytest
"""

from __future__ import annotations

import pytest

from app.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
)
from app.models import CircuitState


# ==
# Helpers
# ==


def successful_operation() -> bool:
    return True


def failing_operation() -> bool:
    raise RuntimeError("failure")


# ==
# Initialization
# ==


def test_breaker_initial_state():

    breaker = CircuitBreaker(
        service="auth",
        failure_threshold=3,
    )

    assert breaker.state == CircuitState.CLOSED

    snapshot = breaker.snapshot()

    assert snapshot["successful_calls"] == 0
    assert snapshot["failed_calls"] == 0
    assert snapshot["consecutive_failures"] == 0


# ==
# Successful Execution
# ==


def test_successful_call():

    breaker = CircuitBreaker(
        service="payments",
        failure_threshold=3,
    )

    result = breaker.call(
        successful_operation
    )

    assert result is True

    snapshot = breaker.snapshot()

    assert snapshot["successful_calls"] == 1
    assert snapshot["failed_calls"] == 0
    assert snapshot["state"] == CircuitState.CLOSED


# ==
# Failed Execution
# ==


def test_failure_is_recorded():

    breaker = CircuitBreaker(
        service="auth",
        failure_threshold=3,
    )

    with pytest.raises(RuntimeError):

        breaker.call(
            failing_operation
        )

    snapshot = breaker.snapshot()

    assert snapshot["failed_calls"] == 1
    assert snapshot["consecutive_failures"] == 1


# ==
# Circuit Opens
# ==


def test_circuit_opens_after_threshold():

    breaker = CircuitBreaker(
        service="orders",
        failure_threshold=2,
    )

    for _ in range(2):

        with pytest.raises(RuntimeError):

            breaker.call(
                failing_operation
            )

    assert breaker.state == CircuitState.OPEN


# ==
# Open Circuit Rejects Calls
# ==


def test_open_circuit_rejects_requests():

    breaker = CircuitBreaker(
        service="orders",
        failure_threshold=1,
    )

    with pytest.raises(RuntimeError):

        breaker.call(
            failing_operation
        )

    assert breaker.state == CircuitState.OPEN

    with pytest.raises(CircuitOpenError):

        breaker.call(
            successful_operation
        )


# ==
# Successful Calls Reset Failure Counter
# ==


def test_success_resets_consecutive_failures():

    breaker = CircuitBreaker(
        service="payments",
        failure_threshold=3,
    )

    with pytest.raises(RuntimeError):

        breaker.call(
            failing_operation
        )

    assert (
        breaker.snapshot()["consecutive_failures"]
        == 1
    )

    breaker.call(
        successful_operation
    )

    snapshot = breaker.snapshot()

    assert snapshot["consecutive_failures"] == 0
    assert snapshot["successful_calls"] == 1


# ==
# Snapshot
# ==


def test_snapshot_contains_expected_fields():

    breaker = CircuitBreaker(
        service="notifications",
        failure_threshold=5,
    )

    snapshot = breaker.snapshot()

    expected = {
        "service",
        "state",
        "successful_calls",
        "failed_calls",
        "consecutive_failures",
    }

    assert expected.issubset(
        snapshot.keys()
    )


# ==
# Multiple Successes
# ==


def test_multiple_successes():

    breaker = CircuitBreaker(
        service="inventory",
        failure_threshold=3,
    )

    for _ in range(10):

        breaker.call(
            successful_operation
        )

    snapshot = breaker.snapshot()

    assert snapshot["successful_calls"] == 10
    assert snapshot["failed_calls"] == 0
    assert snapshot["state"] == CircuitState.CLOSED


# ==
# Mixed Success and Failure
# ==


def test_mixed_execution():

    breaker = CircuitBreaker(
        service="billing",
        failure_threshold=5,
    )

    breaker.call(
        successful_operation
    )

    with pytest.raises(RuntimeError):

        breaker.call(
            failing_operation
        )

    breaker.call(
        successful_operation
    )

    snapshot = breaker.snapshot()

    assert snapshot["successful_calls"] == 2
    assert snapshot["failed_calls"] == 1
    assert snapshot["consecutive_failures"] == 0
    assert breaker.state == CircuitState.CLOSED