"""Pytest configuration and fixtures for MCP module tests."""

import pytest
from amplifier_core import HookResult


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary directory with MCP config structure."""
    amplifier_dir = tmp_path / ".amplifier"
    amplifier_dir.mkdir()
    return amplifier_dir


@pytest.fixture
def sample_mcp_config():
    """Sample MCP server configuration."""
    return {
        "mcpServers": {
            "test-server": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-test"],
                "env": {"TEST_VAR": "${TEST_ENV:-default}"},
            }
        }
    }


@pytest.fixture
def sample_tool_def():
    """Sample MCP tool definition."""
    return {
        "name": "test_tool",
        "description": "A test tool",
        "input_schema": {
            "type": "object",
            "properties": {"input": {"type": "string", "description": "Test input"}},
            "required": ["input"],
        },
    }


@pytest.fixture
def mock_hooks():
    """Mock hooks registry for testing."""

    class MockHooks:
        async def emit(self, event: str, data: dict):
            """Mock emit that does nothing."""
            return HookResult(action="continue", data=data)

    return MockHooks()


@pytest.fixture
def mock_coordinator(mock_hooks):
    """Mock coordinator with hooks."""

    class MockCoordinator:
        def __init__(self):
            self.hooks = mock_hooks

    return MockCoordinator()
