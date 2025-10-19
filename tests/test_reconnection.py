"""Tests for reconnection strategy and circuit breaker functionality."""

import asyncio

import pytest
from amplifier_module_tool_mcp.reconnection import CircuitBreaker
from amplifier_module_tool_mcp.reconnection import ReconnectionConfig
from amplifier_module_tool_mcp.reconnection import ReconnectionStrategy

# Reconnection Strategy Tests


def test_reconnection_config_defaults():
    """Test default reconnection configuration."""
    config = ReconnectionConfig()

    assert config.max_retries == 3
    assert config.initial_delay == 1.0
    assert config.max_delay == 60.0
    assert config.exponential_base == 2.0
    assert config.jitter is True


def test_reconnection_config_custom():
    """Test custom reconnection configuration."""
    config = ReconnectionConfig(max_retries=5, initial_delay=0.5, max_delay=30.0, exponential_base=3.0, jitter=False)

    assert config.max_retries == 5
    assert config.initial_delay == 0.5
    assert config.max_delay == 30.0
    assert config.exponential_base == 3.0
    assert config.jitter is False


def test_calculate_delay():
    """Test delay calculation with exponential backoff."""
    config = ReconnectionConfig(initial_delay=1.0, exponential_base=2.0, max_delay=60.0, jitter=False)
    strategy = ReconnectionStrategy(config)

    # Exponential backoff: 1, 2, 4, 8, 16, 32, 60 (capped)
    assert strategy.calculate_delay(0) == 1.0
    assert strategy.calculate_delay(1) == 2.0
    assert strategy.calculate_delay(2) == 4.0
    assert strategy.calculate_delay(3) == 8.0
    assert strategy.calculate_delay(4) == 16.0
    assert strategy.calculate_delay(5) == 32.0
    assert strategy.calculate_delay(6) == 60.0  # Max cap
    assert strategy.calculate_delay(10) == 60.0  # Still capped


def test_calculate_delay_with_jitter():
    """Test that jitter adds variation to delay."""
    config = ReconnectionConfig(initial_delay=1.0, exponential_base=2.0, jitter=True)
    strategy = ReconnectionStrategy(config)

    # With jitter, delay should vary within range
    delays = [strategy.calculate_delay(2) for _ in range(10)]

    # Should have variation (not all same)
    assert len(set(delays)) > 1

    # All delays should be in reasonable range (4.0 ± 20%)
    for delay in delays:
        assert 3.2 <= delay <= 4.8


@pytest.mark.asyncio
async def test_execute_with_retry_success_immediately():
    """Test successful execution on first try."""
    strategy = ReconnectionStrategy()
    call_count = [0]

    async def operation():
        call_count[0] += 1
        return "success"

    result = await strategy.execute_with_retry(operation, "test_op")

    assert result == "success"
    assert call_count[0] == 1  # Called once


@pytest.mark.asyncio
async def test_execute_with_retry_success_after_failures():
    """Test successful execution after retries."""
    config = ReconnectionConfig(max_retries=3, initial_delay=0.1)
    strategy = ReconnectionStrategy(config)
    call_count = [0]

    async def operation():
        call_count[0] += 1
        if call_count[0] < 3:
            raise RuntimeError(f"Attempt {call_count[0]} failed")
        return "success"

    result = await strategy.execute_with_retry(operation, "test_op")

    assert result == "success"
    assert call_count[0] == 3  # Failed twice, succeeded third time


@pytest.mark.asyncio
async def test_execute_with_retry_all_failures():
    """Test that all retries exhaust and exception is raised."""
    config = ReconnectionConfig(max_retries=2, initial_delay=0.1)
    strategy = ReconnectionStrategy(config)
    call_count = [0]

    async def operation():
        call_count[0] += 1
        raise RuntimeError(f"Attempt {call_count[0]} failed")

    with pytest.raises(RuntimeError, match="failed after 3 attempts"):
        await strategy.execute_with_retry(operation, "test_op")

    assert call_count[0] == 3  # max_retries=2 means 3 total attempts (initial + 2 retries)


# Circuit Breaker Tests


def test_circuit_breaker_initial_state():
    """Test circuit breaker starts in CLOSED state."""
    cb = CircuitBreaker()

    assert cb.state == "CLOSED"
    assert not cb.is_open()


def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures."""
    cb = CircuitBreaker(failure_threshold=3)

    # First 2 failures - should stay closed
    cb.record_failure()
    assert cb.state == "CLOSED"
    cb.record_failure()
    assert cb.state == "CLOSED"

    # Third failure - should open
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.is_open()


def test_circuit_breaker_closes_on_success():
    """Test circuit breaker closes after success."""
    cb = CircuitBreaker()

    # Create some failures
    cb.record_failure()
    cb.record_failure()

    # Success resets failure count
    cb.record_success()

    assert cb.state == "CLOSED"
    assert not cb.is_open()


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_transition():
    """Test circuit breaker transitions from OPEN to HALF_OPEN after timeout."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "OPEN"

    # Wait for recovery timeout
    await asyncio.sleep(0.15)

    # Should transition to HALF_OPEN
    assert cb.state == "HALF_OPEN"


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_to_closed():
    """Test circuit breaker closes from HALF_OPEN after successes."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, success_threshold=2)

    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "OPEN"

    # Wait for recovery timeout
    await asyncio.sleep(0.15)
    assert cb.state == "HALF_OPEN"

    # First success
    cb.record_success()
    assert cb.state == "HALF_OPEN"

    # Second success - should close
    cb.record_success()
    assert cb.state == "CLOSED"


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_to_open():
    """Test circuit breaker reopens from HALF_OPEN on failure."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "OPEN"

    # Wait for recovery timeout
    await asyncio.sleep(0.15)
    assert cb.state == "HALF_OPEN"

    # Failure in HALF_OPEN - should reopen
    cb.record_failure()
    assert cb.state == "OPEN"


def test_circuit_breaker_reset():
    """Test circuit breaker manual reset."""
    cb = CircuitBreaker(failure_threshold=2)

    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "OPEN"

    # Manual reset
    cb.reset()

    assert cb.state == "CLOSED"
    assert not cb.is_open()


def test_circuit_breaker_custom_thresholds():
    """Test circuit breaker with custom thresholds."""
    cb = CircuitBreaker(failure_threshold=5, success_threshold=3)

    # Should take 5 failures to open
    for _ in range(4):
        cb.record_failure()
        assert cb.state == "CLOSED"

    cb.record_failure()
    assert cb.state == "OPEN"
