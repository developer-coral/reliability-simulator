"""
Unit tests for the Retry Handler.

Run with:

    pytest
"""

from __future__ import annotations

import pytest

from app.retry import (
    RetryError,
    RetryHandler,
)


# ==
# Helpers
# ==


class Counter:

    def __init__(self):

        self.calls = 0

    def success(self):

        self.calls += 1

        return True

    def fail(self):

        self.calls += 1

        raise RuntimeError("failure")


# ==
# Successful Execution
# ==


def test_success_first_attempt():

    counter = Counter()

    retry = RetryHandler(
        max_attempts=3,
    )

    result = retry.execute(
        counter.success
    )

    assert result.success is True
    assert result.attempts == 1
    assert counter.calls == 1
    assert result.elapsed_ms >= 0


# ==
# Retry Until Success
# ==


def test_retry_then_success():

    counter = Counter()

    retry = RetryHandler(
        max_attempts=5,
    )

    def flaky():

        counter.calls += 1

        if counter.calls < 3:

            raise RuntimeError(
                "temporary"
            )

        return True

    result = retry.execute(
        flaky
    )

    assert result.success is True
    assert result.attempts == 3
    assert counter.calls == 3


# ==
# Exhaust Retries
# ==


def test_retry_exhausted():

    counter = Counter()

    retry = RetryHandler(
        max_attempts=3,
    )

    with pytest.raises(RetryError):

        retry.execute(
            counter.fail
        )

    assert counter.calls == 3


# ==
# Single Attempt
# ==


def test_single_attempt_configuration():

    counter = Counter()

    retry = RetryHandler(
        max_attempts=1,
    )

    with pytest.raises(RetryError):

        retry.execute(
            counter.fail
        )

    assert counter.calls == 1


# ==
# Many Retries
# ==


def test_max_attempts_respected():

    counter = Counter()

    retry = RetryHandler(
        max_attempts=7,
    )

    with pytest.raises(RetryError):

        retry.execute(
            counter.fail
        )

    assert counter.calls == 7


# ==
# Return Value
# ==


def test_return_value_preserved():

    retry = RetryHandler(
        max_attempts=2,
    )

    result = retry.execute(
        lambda: "hello"
    )

    assert result.success is True


# ==
# Elapsed Time
# ==


def test_elapsed_time_recorded():

    retry = RetryHandler(
        max_attempts=2,
    )

    result = retry.execute(
        lambda: True
    )

    assert result.elapsed_ms >= 0.0


# ==
# Retry Result Fields
# ==


def test_retry_result_fields():

    retry = RetryHandler(
        max_attempts=2,
    )

    result = retry.execute(
        lambda: True
    )

    assert hasattr(
        result,
        "success",
    )

    assert hasattr(
        result,
        "attempts",
    )

    assert hasattr(
        result,
        "elapsed_ms",
    )


# ==
# Exception Propagation
# ==


def test_final_exception_is_retry_error():

    retry = RetryHandler(
        max_attempts=2,
    )

    with pytest.raises(
        RetryError
    ):

        retry.execute(
            lambda: (_ for _ in ()).throw(
                RuntimeError(
                    "boom"
                )
            )
        )


# ==
# Multiple Successful Executions
# ==


def test_multiple_successful_calls():

    retry = RetryHandler(
        max_attempts=3,
    )

    for _ in range(20):

        result = retry.execute(
            lambda: True
        )

        assert result.success is True
        assert result.attempts == 1