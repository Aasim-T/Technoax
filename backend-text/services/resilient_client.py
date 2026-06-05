"""Resilient wrapper around Gemini API calls with retry, circuit breaker, and quota fallback.

Provides exponential backoff with jitter, circuit breaker protection against cascading
failures, and automatic quota-exhaustion detection for graceful degradation.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

from services.gemini_service import GeminiServiceError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"        # Normal operation — requests pass through
    OPEN = "open"            # Tripped — requests are rejected immediately
    HALF_OPEN = "half_open"  # Probing — one request allowed to test recovery


@dataclass
class CircuitBreakerStats:
    """Observable statistics for the circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    total_successes: int = 0
    total_failures: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    last_state_change_time: float | None = None


class CircuitBreaker:
    """
    Thread-safe circuit breaker for Gemini API protection.

    - CLOSED: requests pass through normally
    - OPEN: requests are rejected immediately (fail-fast)
    - HALF_OPEN: a single probe request is allowed; success resets, failure re-opens
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        name: str = "gemini",
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_seconds
        self._name = name

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._total_successes = 0
        self._total_failures = 0
        self._last_failure_time: float | None = None
        self._last_success_time: float | None = None
        self._last_state_change_time: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        return CircuitBreakerStats(
            state=self._state,
            consecutive_failures=self._consecutive_failures,
            total_successes=self._total_successes,
            total_failures=self._total_failures,
            last_failure_time=self._last_failure_time,
            last_success_time=self._last_success_time,
            last_state_change_time=self._last_state_change_time,
        )

    async def can_execute(self) -> bool:
        """Check if a request is allowed under the current circuit state."""
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self._transition_to(CircuitState.HALF_OPEN)
                    logger.info(
                        "Circuit breaker [%s] transitioning to HALF_OPEN for probe",
                        self._name,
                    )
                    return True
                return False

            # HALF_OPEN — allow one probe
            return True

    async def record_success(self) -> None:
        """Record a successful API call — resets the circuit to CLOSED."""
        async with self._lock:
            self._consecutive_failures = 0
            self._total_successes += 1
            self._last_success_time = time.monotonic()

            if self._state != CircuitState.CLOSED:
                logger.info(
                    "Circuit breaker [%s] recovered → CLOSED (total_successes=%d)",
                    self._name,
                    self._total_successes,
                )
                self._transition_to(CircuitState.CLOSED)

    async def record_failure(self, error: Exception | None = None) -> None:
        """Record a failed API call — may trip the circuit to OPEN."""
        async with self._lock:
            self._consecutive_failures += 1
            self._total_failures += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                logger.warning(
                    "Circuit breaker [%s] probe failed → OPEN (error=%s)",
                    self._name,
                    error,
                )
                self._transition_to(CircuitState.OPEN)
            elif self._consecutive_failures >= self._failure_threshold:
                logger.warning(
                    "Circuit breaker [%s] tripped → OPEN after %d consecutive failures",
                    self._name,
                    self._consecutive_failures,
                )
                self._transition_to(CircuitState.OPEN)

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to probe recovery."""
        if self._last_failure_time is None:
            return True
        elapsed = time.monotonic() - self._last_failure_time
        return elapsed >= self._recovery_timeout

    def _transition_to(self, new_state: CircuitState) -> None:
        self._state = new_state
        self._last_state_change_time = time.monotonic()


def _is_quota_error(exc: Exception) -> bool:
    """Detect quota exhaustion / rate-limit errors from Gemini API."""
    error_str = str(exc).lower()
    quota_indicators = ("429", "quota", "rate limit", "resource exhausted", "too many requests")
    return any(indicator in error_str for indicator in quota_indicators)


def _is_retryable_error(exc: Exception) -> bool:
    """Determine if an error is worth retrying (transient failures)."""
    error_str = str(exc).lower()
    retryable_indicators = (
        "timeout", "503", "500", "502", "504",
        "connection", "unavailable", "internal",
    )
    return any(indicator in error_str for indicator in retryable_indicators)


async def execute_with_resilience(
    func: Callable[..., T],
    *args: Any,
    circuit_breaker: CircuitBreaker,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 8.0,
    operation_name: str = "gemini_call",
    **kwargs: Any,
) -> T:
    """
    Execute a synchronous function with retry logic and circuit breaker protection.

    Retry strategy:
    - Exponential backoff with jitter
    - Quota errors → immediate fallback (no retry)
    - Transient errors → retry with backoff
    - Circuit open → immediate fallback

    Args:
        func: The synchronous callable to execute.
        circuit_breaker: Circuit breaker instance for this service.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds before first retry.
        max_delay: Maximum delay cap in seconds.
        operation_name: Human-readable label for logging.

    Returns:
        The result of the function call.

    Raises:
        GeminiServiceError: When all retries are exhausted or circuit is open.
    """
    if not await circuit_breaker.can_execute():
        raise GeminiServiceError(
            f"Circuit breaker is OPEN for {operation_name} — using fallback. "
            f"Recovery probe in ~{30}s."
        )

    last_exception: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            result = func(*args, **kwargs)
            await circuit_breaker.record_success()
            logger.debug(
                "%s succeeded on attempt %d/%d",
                operation_name,
                attempt,
                max_retries,
            )
            return result

        except Exception as exc:
            last_exception = exc

            # Quota errors: don't retry, fail fast
            if _is_quota_error(exc):
                logger.warning(
                    "%s quota exhausted (attempt %d/%d): %s — skipping retries",
                    operation_name,
                    attempt,
                    max_retries,
                    exc,
                )
                await circuit_breaker.record_failure(exc)
                raise GeminiServiceError(
                    f"Gemini quota exhausted for {operation_name}",
                    cause=exc,
                ) from exc

            # Non-retryable errors: record failure and raise
            if not _is_retryable_error(exc) and attempt > 1:
                logger.warning(
                    "%s non-retryable error (attempt %d/%d): %s",
                    operation_name,
                    attempt,
                    max_retries,
                    exc,
                )
                await circuit_breaker.record_failure(exc)
                raise GeminiServiceError(
                    f"{operation_name} failed with non-retryable error",
                    cause=exc,
                ) from exc

            # Retryable: apply backoff
            if attempt < max_retries:
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                jitter = random.uniform(0, delay * 0.3)
                total_delay = delay + jitter
                logger.info(
                    "%s transient error (attempt %d/%d): %s — retrying in %.1fs",
                    operation_name,
                    attempt,
                    max_retries,
                    exc,
                    total_delay,
                )
                await asyncio.sleep(total_delay)
            else:
                logger.warning(
                    "%s exhausted all %d retries: %s",
                    operation_name,
                    max_retries,
                    exc,
                )
                await circuit_breaker.record_failure(exc)

    raise GeminiServiceError(
        f"{operation_name} failed after {max_retries} attempts",
        cause=last_exception,
    )


# Module-level singleton circuit breaker for the Gemini service
_gemini_circuit_breaker: CircuitBreaker | None = None


def get_gemini_circuit_breaker() -> CircuitBreaker:
    """Return the singleton Gemini circuit breaker instance."""
    global _gemini_circuit_breaker
    if _gemini_circuit_breaker is None:
        _gemini_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout_seconds=30.0,
            name="gemini",
        )
    return _gemini_circuit_breaker
