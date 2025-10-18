"""Pytest configuration and fixtures for MCP module tests."""

import pytest


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
