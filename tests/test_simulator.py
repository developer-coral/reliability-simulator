"""
Unit tests for the Reliability Simulator.

Run with:

    pytest
"""

from __future__ import annotations

from app.models import (
    CircuitState,
    SimulationRequest,
)
from app.simulator import (
    ReliabilitySimulator,
)


# ==
# Helpers
# ==


def default_request(**kwargs) -> SimulationRequest:
    """
    Create a SimulationRequest with sensible defaults.
    """

    data = {
        "services": [
            "auth",
            "payments",
        ],
        "iterations": 10,
        "failure_rate": 0.20,
        "retry_attempts": 3,
        "breaker_threshold": 3,
        "latency_ms": 50,
        "random_seed": 42,
    }

    data.update(kwargs)

    return SimulationRequest(**data)


# ==
# Construction
# ==


def test_simulator_initializes():

    simulator = ReliabilitySimulator(
        default_request()
    )

    assert simulator is not None

    assert len(simulator.breakers) == 2

    assert len(simulator.chaos) == 2


# ==
# Successful Simulation
# ==


def test_run_returns_result():

    simulator = ReliabilitySimulator(
        default_request(
            failure_rate=0.0
        )
    )

    result = simulator.run()

    assert result.statistics.total_requests == 20

    assert (
        result.statistics.failed_requests
        == 0
    )

    assert (
        result.statistics.successful_requests
        == 20
    )

    assert len(
        result.traces
    ) == 20


# ==
# Failures Are Recorded
# ==


def test_failures_are_present():

    simulator = ReliabilitySimulator(
        default_request(
            failure_rate=1.0,
            retry_attempts=1,
        )
    )

    result = simulator.run()

    assert (
        result.statistics.failed_requests
        > 0
    )


# ==
# Circuit Breakers Exist
# ==


def test_circuit_breakers_returned():

    simulator = ReliabilitySimulator(
        default_request()
    )

    result = simulator.run()

    assert len(
        result.circuit_breakers
    ) == 2


# ==
# Trace Count
# ==


def test_trace_count_matches_requests():

    request = default_request(
        iterations=25,
        services=[
            "a",
            "b",
            "c",
        ],
        failure_rate=0.0,
    )

    simulator = ReliabilitySimulator(
        request
    )

    result = simulator.run()

    expected = (
        request.iterations
        * len(request.services)
    )

    assert len(
        result.traces
    ) == expected


# ==
# Success Rate
# ==


def test_success_rate_without_failures():

    simulator = ReliabilitySimulator(
        default_request(
            failure_rate=0.0
        )
    )

    result = simulator.run()

    assert (
        result.statistics.success_rate
        == 1.0
    )

    assert (
        result.statistics.failure_rate
        == 0.0
    )


# ==
# Average Latency
# ==


def test_average_latency_is_non_negative():

    simulator = ReliabilitySimulator(
        default_request()
    )

    result = simulator.run()

    assert (
        result.statistics.average_latency_ms
        >= 0
    )


# ==
# Circuit Snapshot
# ==


def test_snapshot_contains_services():

    simulator = ReliabilitySimulator(
        default_request()
    )

    result = simulator.run()

    services = {
        snapshot.service
        for snapshot in result.circuit_breakers
    }

    assert services == {
        "auth",
        "payments",
    }


# ==
# Circuit Opens Under Heavy Failure
# ==


def test_circuit_opens_when_failures_are_constant():

    simulator = ReliabilitySimulator(
        default_request(
            failure_rate=1.0,
            retry_attempts=1,
            breaker_threshold=1,
            iterations=5,
        )
    )

    result = simulator.run()

    assert any(
        snapshot.state == CircuitState.OPEN
        for snapshot in result.circuit_breakers
    )


# ==
# Deterministic Execution
# ==


def test_seed_produces_repeatable_results():

    request = default_request(
        random_seed=123,
    )

    first = ReliabilitySimulator(
        request
    ).run()

    second = ReliabilitySimulator(
        request
    ).run()

    assert (
        first.statistics.total_requests
        ==
        second.statistics.total_requests
    )

    assert (
        first.statistics.successful_requests
        ==
        second.statistics.successful_requests
    )

    assert (
        first.statistics.failed_requests
        ==
        second.statistics.failed_requests
    )

    assert (
        first.statistics.success_rate
        ==
        second.statistics.success_rate
    )