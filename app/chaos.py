"""
Chaos engineering module.

Injects deterministic failures into the simulator to emulate
unreliable distributed systems.

Supported failures

- Timeout
- Connection failure
- Internal server error
- Artificial latency
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .models import FailureType


# ==
# Exceptions
# ==


class ChaosError(Exception):
    """Base chaos exception."""


class InjectedTimeoutError(TimeoutError):
    """Injected timeout."""


class InjectedConnectionError(ConnectionError):
    """Injected network failure."""


class InjectedServerError(RuntimeError):
    """Injected HTTP 500 equivalent."""


# ==
# Configuration
# ==


@dataclass(slots=True)
class ChaosConfig:
    """
    Configuration for one service.
    """

    failure_rate: float = 0.15

    latency_ms: int = 100

    timeout_weight: float = 0.40

    connection_weight: float = 0.30

    server_weight: float = 0.30


# ==
# Statistics
# ==


@dataclass(slots=True)
class ChaosStatistics:

    total_requests: int = 0

    injected_failures: int = 0

    latency_events: int = 0

    timeout_failures: int = 0

    connection_failures: int = 0

    server_failures: int = 0

    successful_requests: int = 0


# ==
# Chaos Injector
# ==


class ChaosInjector:
    """
    Deterministic chaos injector.

    A seeded random generator guarantees reproducible
    simulation runs.
    """

    def __init__(
        self,
        config: ChaosConfig,
        seed: int | None = None,
    ) -> None:

        self.config = config

        self.random = random.Random(seed)

        self.statistics = ChaosStatistics()

    # ---------------------------------------------------------

    def inject(self) -> FailureType:
        """
        Execute one simulated request.

        Returns the injected failure type.
        """

        self.statistics.total_requests += 1

        self._inject_latency()

        if self.random.random() > self.config.failure_rate:

            self.statistics.successful_requests += 1

            return FailureType.NONE

        failure = self._choose_failure()

        self.statistics.injected_failures += 1

        if failure == FailureType.TIMEOUT:

            self.statistics.timeout_failures += 1

            raise InjectedTimeoutError(
                "Injected timeout."
            )

        if failure == FailureType.CONNECTION:

            self.statistics.connection_failures += 1

            raise InjectedConnectionError(
                "Injected connection failure."
            )

        self.statistics.server_failures += 1

        raise InjectedServerError(
            "Injected server failure."
        )

    # ---------------------------------------------------------

    def _inject_latency(self) -> None:
        """
        Simulate network latency.
        """

        if self.config.latency_ms <= 0:
            return

        delay = self.random.uniform(
            0,
            self.config.latency_ms,
        )

        self.statistics.latency_events += 1

        time.sleep(delay / 1000)

    # ---------------------------------------------------------

    def _choose_failure(self) -> FailureType:

        value = self.random.random()

        if value <= self.config.timeout_weight:
            return FailureType.TIMEOUT

        if (
            value
            <= self.config.timeout_weight
            + self.config.connection_weight
        ):
            return FailureType.CONNECTION

        return FailureType.SERVER_ERROR

    # ---------------------------------------------------------

    def reset(self) -> None:

        self.statistics = ChaosStatistics()

    # ---------------------------------------------------------

    def snapshot(self) -> dict:
        """
        Return current statistics.
        """

        return {
            "total_requests": self.statistics.total_requests,
            "successful_requests": self.statistics.successful_requests,
            "failures": self.statistics.injected_failures,
            "latency_events": self.statistics.latency_events,
            "timeouts": self.statistics.timeout_failures,
            "connections": self.statistics.connection_failures,
            "server_errors": self.statistics.server_failures,
        }

    # ---------------------------------------------------------

    def __repr__(self) -> str:

        return (
            "ChaosInjector("
            f"failure_rate={self.config.failure_rate}, "
            f"latency_ms={self.config.latency_ms})"
        )