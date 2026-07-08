"""
Retry handler with exponential backoff.

The retry handler is responsible for recovering from transient
failures while respecting the Circuit Breaker.

Features
--------
- Configurable retry attempts
- Exponential backoff
- Optional jitter
- Retry statistics
- Circuit Breaker integration
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from .circuit_breaker import CircuitBreaker

T = TypeVar("T")


# ==
# Exceptions
# ==


class RetryError(Exception):
    """Raised when all retry attempts fail."""


# ==
# Result
# ==


@dataclass(slots=True)
class RetryResult:
    """
    Metadata describing a retry execution.
    """

    result: Any | None

    attempts: int

    success: bool

    elapsed_ms: float


# ==
# Retry Handler
# ==


class RetryHandler:
    """
    Retry failed operations using exponential backoff.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 0.2,
        backoff_factor: float = 2.0,
        max_delay: float = 5.0,
        jitter: bool = True,
    ) -> None:

        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.jitter = jitter

    # ---------------------------------------------------------

    def _sleep_time(
        self,
        attempt: int,
    ) -> float:
        """
        Calculate exponential backoff delay.
        """

        delay = min(
            self.initial_delay
            * (self.backoff_factor ** (attempt - 1)),
            self.max_delay,
        )

        if self.jitter:
            delay *= random.uniform(0.8, 1.2)

        return delay

    # ---------------------------------------------------------

    def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        breaker: CircuitBreaker | None = None,
        **kwargs: Any,
    ) -> RetryResult:
        """
        Execute a callable with retry support.
        """

        started = time.perf_counter()

        last_exception: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):

            try:

                if breaker is None:
                    result = func(*args, **kwargs)
                else:
                    result = breaker.call(
                        func,
                        *args,
                        **kwargs,
                    )

                elapsed = (
                    time.perf_counter() - started
                ) * 1000

                return RetryResult(
                    result=result,
                    attempts=attempt,
                    success=True,
                    elapsed_ms=elapsed,
                )

            except Exception as exc:

                last_exception = exc

                if attempt >= self.max_attempts:
                    break

                time.sleep(
                    self._sleep_time(attempt)
                )

        elapsed = (
            time.perf_counter() - started
        ) * 1000

        raise RetryError(
            f"Operation failed after "
            f"{self.max_attempts} attempts."
        ) from last_exception

    # ---------------------------------------------------------

    def __repr__(self) -> str:

        return (
            "RetryHandler("
            f"max_attempts={self.max_attempts}, "
            f"initial_delay={self.initial_delay}, "
            f"backoff_factor={self.backoff_factor})"
        )