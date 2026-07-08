"""
Simulation engine.

Coordinates

- Chaos Injection
- Retry Handler
- Circuit Breaker
- Metrics Collection

Part 1

Provides

- ReliabilitySimulator
- initialization
- helper methods
- mock service

Simulation loop is implemented in Part 2.
"""

from __future__ import annotations

import random
import time
from typing import Callable

from .chaos import (
    ChaosConfig,
    ChaosInjector,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
)
from .metrics import (
    MetricsCollector,
)
from .models import (
    CircuitState,
    FailureType,
    SimulationRequest,
    TraceEntry,
)
from .retry import (
    RetryError,
    RetryHandler,
)


# ==
# Reliability Simulator
# ==


class ReliabilitySimulator:
    """
    Main orchestration engine.

    One simulator instance executes one simulation request.
    """

    def __init__(
        self,
        request: SimulationRequest,
    ) -> None:

        self.request = request

        self.random = random.Random(
            request.random_seed
        )

        self.metrics = MetricsCollector()

        self.retry = RetryHandler(
            max_attempts=request.retry_attempts,
        )

        self.breakers = {
            service: CircuitBreaker(
                service=service,
                failure_threshold=request.breaker_threshold,
            )
            for service in request.services
        }

        self.chaos = {
            service: ChaosInjector(
                ChaosConfig(
                    failure_rate=request.failure_rate,
                    latency_ms=request.latency_ms,
                ),
                seed=request.random_seed,
            )
            for service in request.services
        }

    # =========================================================
    # Mock Service
    # =========================================================

    @staticmethod
    def _mock_service() -> bool:
        """
        Represents the downstream service.

        ChaosInjector is responsible for failures,
        therefore this service always succeeds.
        """

        return True

    # =========================================================
    # Helper Methods
    # =========================================================

    def _breaker(
        self,
        service: str,
    ) -> CircuitBreaker:

        return self.breakers[service]

    def _inject_failure(
        self,
        service: str,
    ) -> FailureType:
        """
        Execute chaos injection.

        Returns the injected failure type.

        Raises one of the injected exceptions when
        a failure occurs.
        """

        return self.chaos[
            service
        ].inject()

    def _measure(
        self,
        operation: Callable[[], bool],
    ) -> tuple[bool, float]:
        """
        Measure execution latency.
        """

        started = time.perf_counter()

        result = operation()

        elapsed = (
            time.perf_counter() - started
        ) * 1000

        return result, elapsed

    def _execute_service(
        self,
        service: str,
    ) -> tuple[bool, float, int]:
        """
        Execute one protected request.

        Returns

        (
            success,
            latency_ms,
            retry_attempts
        )
        """

        breaker = self._breaker(service)

        def operation() -> bool:

            self._inject_failure(service)

            return self._mock_service()

        result = self.retry.execute(
            operation,
            breaker=breaker,
        )

        return (
            result.success,
            result.elapsed_ms,
            result.attempts - 1,
        )

    # =========================================================
    # Trace Helper
    # =========================================================

    def _trace(
        self,
        *,
        iteration: int,
        service: str,
        success: bool,
        latency_ms: float,
        retries: int,
        failure: FailureType,
        message: str,
    ) -> TraceEntry:

        breaker = self._breaker(service)

        return TraceEntry(
            iteration=iteration,
            service=service,
            success=success,
            latency_ms=round(
                latency_ms,
                2,
            ),
            retries=retries,
            circuit_state=breaker.state,
            failure=failure,
            message=message,
        )

    # =========================================================
    # Metrics Helpers
    # =========================================================

    def _record_success(
        self,
        trace: TraceEntry,
    ) -> None:

        self.metrics.record_success(
            latency_ms=trace.latency_ms,
            retries=trace.retries,
        )

        self.metrics.record_trace(trace)

    def _record_failure(
        self,
        trace: TraceEntry,
    ) -> None:

        self.metrics.record_failure(
            latency_ms=trace.latency_ms,
            retries=trace.retries,
        )

        self.metrics.record_trace(trace)

        if trace.circuit_state == CircuitState.OPEN:
            self.metrics.record_circuit_open()

        # =========================================================
    # Public API
    # =========================================================

    def run(self):
        """
        Execute the complete simulation.
        """

        for iteration in range(1, self.request.iterations + 1):

            for service in self.request.services:

                try:

                    success, latency, retries = (
                        self._execute_service(service)
                    )

                    trace = self._trace(
                        iteration=iteration,
                        service=service,
                        success=success,
                        latency_ms=latency,
                        retries=retries,
                        failure=FailureType.NONE,
                        message="Request completed successfully.",
                    )

                    self._record_success(trace)

                except CircuitOpenError:

                    trace = self._trace(
                        iteration=iteration,
                        service=service,
                        success=False,
                        latency_ms=0.0,
                        retries=0,
                        failure=FailureType.NONE,
                        message="Circuit breaker is OPEN.",
                    )

                    self._record_failure(trace)

                except RetryError:

                    breaker = self._breaker(service)

                    if breaker.state == CircuitState.OPEN:
                        self.metrics.record_circuit_open()

                    trace = self._trace(
                        iteration=iteration,
                        service=service,
                        success=False,
                        latency_ms=0.0,
                        retries=self.retry.max_attempts,
                        failure=FailureType.SERVER_ERROR,
                        message="Retry attempts exhausted.",
                    )

                    self._record_failure(trace)

                except TimeoutError:

                    trace = self._trace(
                        iteration=iteration,
                        service=service,
                        success=False,
                        latency_ms=0.0,
                        retries=0,
                        failure=FailureType.TIMEOUT,
                        message="Injected timeout.",
                    )

                    self._record_failure(trace)

                except ConnectionError:

                    trace = self._trace(
                        iteration=iteration,
                        service=service,
                        success=False,
                        latency_ms=0.0,
                        retries=0,
                        failure=FailureType.CONNECTION,
                        message="Injected connection failure.",
                    )

                    self._record_failure(trace)

                except Exception as exc:

                    trace = self._trace(
                        iteration=iteration,
                        service=service,
                        success=False,
                        latency_ms=0.0,
                        retries=0,
                        failure=FailureType.SERVER_ERROR,
                        message=str(exc),
                    )

                    self._record_failure(trace)

        from .metrics import build_result

        return build_result(
            self.metrics,
            self.breakers,
        )