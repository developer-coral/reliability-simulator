"""
Metrics aggregation for the Reliability Simulator.

This module collects runtime metrics during a simulation and
produces the final API response models.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .circuit_breaker import CircuitBreaker
from .models import (
    CircuitSnapshot,
    SimulationResult,
    SimulationStatistics,
    TraceEntry,
)


# ==
# Metrics Collector
# ==


@dataclass(slots=True)
class MetricsCollector:
    """
    Collects metrics throughout a simulation run.
    """

    total_requests: int = 0

    successful_requests: int = 0

    failed_requests: int = 0

    retries: int = 0

    circuit_opens: int = 0

    total_latency_ms: float = 0.0

    traces: list[TraceEntry] = field(
        default_factory=list
    )

    # ---------------------------------------------------------

    def record_success(
        self,
        latency_ms: float,
        retries: int = 0,
    ) -> None:

        self.total_requests += 1

        self.successful_requests += 1

        self.total_latency_ms += latency_ms

        self.retries += retries

    # ---------------------------------------------------------

    def record_failure(
        self,
        latency_ms: float,
        retries: int = 0,
    ) -> None:

        self.total_requests += 1

        self.failed_requests += 1

        self.total_latency_ms += latency_ms

        self.retries += retries

    # ---------------------------------------------------------

    def record_trace(
        self,
        trace: TraceEntry,
    ) -> None:

        self.traces.append(trace)

    # ---------------------------------------------------------

    def record_circuit_open(self) -> None:

        self.circuit_opens += 1

    # ---------------------------------------------------------

    @property
    def success_rate(self) -> float:

        if self.total_requests == 0:
            return 0.0

        return self.successful_requests / self.total_requests

    # ---------------------------------------------------------

    @property
    def failure_rate(self) -> float:

        if self.total_requests == 0:
            return 0.0

        return self.failed_requests / self.total_requests

    # ---------------------------------------------------------

    @property
    def average_latency_ms(self) -> float:

        if self.total_requests == 0:
            return 0.0

        return (
            self.total_latency_ms
            / self.total_requests
        )

    # ---------------------------------------------------------

    def build_statistics(
        self,
    ) -> SimulationStatistics:
        """
        Convert runtime counters into the API model.
        """

        return SimulationStatistics(
            total_requests=self.total_requests,
            successful_requests=self.successful_requests,
            failed_requests=self.failed_requests,
            retries=self.retries,
            circuit_opens=self.circuit_opens,
            average_latency_ms=round(
                self.average_latency_ms,
                2,
            ),
            success_rate=round(
                self.success_rate,
                4,
            ),
            failure_rate=round(
                self.failure_rate,
                4,
            ),
        )


# ==
# Helpers
# ==


def build_circuit_snapshots(
    breakers: dict[str, CircuitBreaker],
) -> list[CircuitSnapshot]:
    """
    Convert all circuit breakers into response models.
    """

    snapshots: list[CircuitSnapshot] = []

    for breaker in breakers.values():

        data = breaker.snapshot()

        snapshots.append(
            CircuitSnapshot(
                service=data["service"],
                state=data["state"],
                successful_calls=data[
                    "successful_calls"
                ],
                failed_calls=data[
                    "failed_calls"
                ],
                consecutive_failures=data[
                    "consecutive_failures"
                ],
            )
        )

    return snapshots


# ==
# Result Builder
# ==


def build_result(
    metrics: MetricsCollector,
    breakers: dict[str, CircuitBreaker],
) -> SimulationResult:
    """
    Assemble the complete simulation response.
    """

    return SimulationResult(
        statistics=metrics.build_statistics(),
        circuit_breakers=build_circuit_snapshots(
            breakers
        ),
        traces=metrics.traces,
    )