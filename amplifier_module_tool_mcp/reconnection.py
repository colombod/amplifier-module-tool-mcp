"""Reconnection strategy with exponential backoff for MCP clients."""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class ReconnectionConfig:
    """Configuration for reconnection behavior."""

    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd


class ReconnectionStrategy:
    """
    Implements exponential backoff reconnection strategy.

    Features:
    - Exponential backoff with configurable base
    - Maximum delay cap
    - Optional jitter to prevent thundering herd
    - Per-operation retry tracking
    """

    def __init__(self, config: ReconnectionConfig | None = None):
        """
        Initialize reconnection strategy.

        Args:
            config: Reconnection configuration (uses defaults if None)
        """
        self.config = config or ReconnectionConfig()
        self._retry_count = 0

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given retry attempt.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: initial_delay * (base ^ attempt)
        delay = self.config.initial_delay * (self.config.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, self.config.max_delay)

        # Add jitter if enabled (random 0-20% variation)
        if self.config.jitter:
            import random

            jitter_factor = random.uniform(0.8, 1.2)
            delay *= jitter_factor

        return delay

    async def execute_with_retry(self, operation: Callable[[], Any], operation_name: str = "operation") -> Any:
        """
        Execute operation with retry logic.

        Args:
            operation: Async callable to execute
            operation_name: Name for logging

        Returns:
            Result from operation

        Raises:
            Exception: If all retries exhausted
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.calculate_delay(attempt - 1)
                    logger.info(
                        f"Retry {attempt}/{self.config.max_retries} for {operation_name} after {delay:.2f}s delay"
                    )
                    await asyncio.sleep(delay)

                result = await operation()
                if attempt > 0:
                    logger.info(f"{operation_name} succeeded after {attempt} retries")
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"{operation_name} failed (attempt {attempt + 1}): {e}")

                # Don't retry on last attempt
                if attempt >= self.config.max_retries:
                    break

        # All retries exhausted
        logger.error(f"{operation_name} failed after {self.config.max_retries + 1} attempts")
        raise RuntimeError(f"{operation_name} failed after {self.config.max_retries + 1} attempts") from last_error

    def reset(self) -> None:
        """Reset retry counter."""
        self._retry_count = 0


class CircuitBreaker:
    """
    Simple circuit breaker to prevent repeated connection attempts to failing servers.

    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying half-open
            success_threshold: Successes in half-open before closing
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._failure_count = 0
        self._success_count = 0
        self._state = "CLOSED"
        self._opened_at: float | None = None

    @property
    def state(self) -> str:
        """Get current circuit state."""
        # Check if we should transition from OPEN to HALF_OPEN
        if self._state == "OPEN" and self._opened_at:
            import time

            if time.time() - self._opened_at >= self.recovery_timeout:
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                self._state = "HALF_OPEN"
                self._success_count = 0

        return self._state

    def record_success(self) -> None:
        """Record a successful operation."""
        self._failure_count = 0

        if self._state == "HALF_OPEN":
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                logger.info("Circuit breaker closing after recovery")
                self._state = "CLOSED"
                self._success_count = 0

    def record_failure(self) -> None:
        """Record a failed operation."""
        self._failure_count += 1

        if self._state == "HALF_OPEN":
            logger.info("Circuit breaker reopening after failure in HALF_OPEN")
            self._state = "OPEN"
            import time

            self._opened_at = time.time()
            self._success_count = 0

        elif self._state == "CLOSED":
            if self._failure_count >= self.failure_threshold:
                logger.warning(f"Circuit breaker opening after {self._failure_count} failures")
                self._state = "OPEN"
                import time

                self._opened_at = time.time()

    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self.state == "OPEN"

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self._state = "CLOSED"
        self._failure_count = 0
        self._success_count = 0
        self._opened_at = None
