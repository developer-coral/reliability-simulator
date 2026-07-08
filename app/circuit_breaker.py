"""
Circuit Breaker implementation.

States

CLOSED
    Normal operation.

OPEN
    Requests are rejected until the recovery timeout expires.

HALF_OPEN
    A trial request is allowed. Success closes the circuit.
    Failure reopens it.
"""

from __future__ import annotations

import time
from typing import Any, Callable, TypeVar

from .models import CircuitState

T = TypeVar("T")


# ==
# Exceptions
# ==


class CircuitBreakerError(Exception):
    """Base circuit breaker exception."""


class CircuitOpenError(CircuitBreakerError):
    """Raised when the circuit is open."""


# ==
# Circuit Breaker
# ==


class CircuitBreaker:
    """
    Simple circuit breaker implementation.

    Example
    -------
    >>> breaker = CircuitBreaker("payments")
    >>> result = breaker.call(fetch_payment)
    """

    def __init__(
        self,
        service: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 5.0,
    ) -> None:

        self.service = service

        self.failure_threshold = failure_threshold

        self.recovery_timeout = recovery_timeout

        self.state = CircuitState.CLOSED

        self.consecutive_failures = 0

        self.successful_calls = 0

        self.failed_calls = 0

        self._opened_at = 0.0

    # ---------------------------------------------------------
    # State transitions
    # ---------------------------------------------------------

    def _open(self) -> None:

        self.state = CircuitState.OPEN

        self._opened_at = time.monotonic()

    def _close(self) -> None:

        self.state = CircuitState.CLOSED

        self.consecutive_failures = 0

    def _half_open(self) -> None:

        self.state = CircuitState.HALF_OPEN

    # ---------------------------------------------------------
    # Request permission
    # ---------------------------------------------------------

    def allow_request(self) -> bool:
        """
        Returns True when a request may proceed.
        """

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.HALF_OPEN:
            return True

        elapsed = time.monotonic() - self._opened_at

        if elapsed >= self.recovery_timeout:

            self._half_open()

            return True

        return False

    # ---------------------------------------------------------
    # Recording
    # ---------------------------------------------------------

    def record_success(self) -> None:

        self.successful_calls += 1

        self.consecutive_failures = 0

        if self.state == CircuitState.HALF_OPEN:
            self._close()

    def record_failure(self) -> None:

        self.failed_calls += 1

        self.consecutive_failures += 1

        if (
            self.state == CircuitState.HALF_OPEN
            or self.consecutive_failures >= self.failure_threshold
        ):
            self._open()

    # ---------------------------------------------------------
    # Protected execution
    # ---------------------------------------------------------

    def call(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute a protected function.
        """

        if not self.allow_request():

            raise CircuitOpenError(
                f"Circuit '{self.service}' is OPEN."
            )

        try:

            result = func(*args, **kwargs)

        except Exception:

            self.record_failure()

            raise

        self.record_success()

        return result

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def is_open(self) -> bool:

        return self.state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:

        return self.state == CircuitState.CLOSED

    @property
    def is_half_open(self) -> bool:

        return self.state == CircuitState.HALF_OPEN

    # ---------------------------------------------------------

    def reset(self) -> None:
        """
        Reset the breaker.
        """

        self.state = CircuitState.CLOSED

        self.consecutive_failures = 0

        self.successful_calls = 0

        self.failed_calls = 0

        self._opened_at = 0.0

    # ---------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """
        Return the current breaker state.
        """

        return {
            "service": self.service,
            "state": self.state,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "consecutive_failures": self.consecutive_failures,
        }

    # ---------------------------------------------------------

    def __repr__(self) -> str:

        return (
            "CircuitBreaker("
            f"service='{self.service}', "
            f"state='{self.state.value}', "
            f"failures={self.consecutive_failures})"
        )