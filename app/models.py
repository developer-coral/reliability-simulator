"""
Shared domain models for the Reliability Simulator.

These models define the request/response contracts used by the
FastAPI API and the internal simulator.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==
# Enums
# ==


class CircuitState(str, Enum):
    """Circuit breaker state."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class FailureType(str, Enum):
    """Possible injected failures."""

    NONE = "none"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    SERVER_ERROR = "server_error"
    LATENCY = "latency"


# ==
# Simulation Request
# ==


class SimulationRequest(BaseModel):
    """
    Input received by POST /simulate.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    services: list[str] = Field(
        default_factory=lambda: [
            "auth",
            "payments",
            "notifications",
        ],
        min_length=1,
        description="Services participating in the simulation.",
    )

    iterations: int = Field(
        default=50,
        ge=1,
        le=10000,
        description="Number of requests sent to each service.",
    )

    failure_rate: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Probability that a request fails.",
    )

    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
    )

    breaker_threshold: int = Field(
        default=3,
        ge=1,
        le=20,
    )

    latency_ms: int = Field(
        default=100,
        ge=0,
        le=5000,
    )

    random_seed: int | None = Field(
        default=42,
    )

    @field_validator("services")
    @classmethod
    def validate_services(
        cls,
        value: list[str],
    ) -> list[str]:

        cleaned = []

        for service in value:

            service = service.strip().lower()

            if not service:
                raise ValueError(
                    "Service names cannot be empty."
                )

            cleaned.append(service)

        return cleaned


# ==
# Trace
# ==


class TraceEntry(BaseModel):
    """
    One simulated request.
    """

    model_config = ConfigDict(frozen=True)

    iteration: int

    service: str

    success: bool

    latency_ms: float

    retries: int = 0

    circuit_state: CircuitState

    failure: FailureType = FailureType.NONE

    message: str


# ==
# Circuit Snapshot
# ==


class CircuitSnapshot(BaseModel):
    """
    Final circuit breaker state.
    """

    service: str

    state: CircuitState

    successful_calls: int

    failed_calls: int

    consecutive_failures: int


# ==
# Statistics
# ==


class SimulationStatistics(BaseModel):

    total_requests: int

    successful_requests: int

    failed_requests: int

    retries: int

    circuit_opens: int

    average_latency_ms: float

    success_rate: float

    failure_rate: float


# ==
# Response
# ==


class SimulationResult(BaseModel):
    """
    Response returned by POST /simulate.
    """

    statistics: SimulationStatistics

    circuit_breakers: list[CircuitSnapshot]

    traces: list[TraceEntry]


# ==
# Runtime Metrics
# ==


class Metrics(BaseModel):
    """
    Internal mutable metrics object.
    """

    model_config = ConfigDict(validate_assignment=True)

    total_requests: int = 0

    successful_requests: int = 0

    failed_requests: int = 0

    retries: int = 0

    circuit_opens: int = 0

    total_latency_ms: float = 0.0

    def success_rate(self) -> float:

        if self.total_requests == 0:
            return 0.0

        return self.successful_requests / self.total_requests

    def failure_rate(self) -> float:

        if self.total_requests == 0:
            return 0.0

        return self.failed_requests / self.total_requests

    def average_latency(self) -> float:

        if self.total_requests == 0:
            return 0.0

        return self.total_latency_ms / self.total_requests