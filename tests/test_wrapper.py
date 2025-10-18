"""Tests for MCP tool wrapper."""

import pytest
from amplifier_module_tool_mcp.wrapper import MCPToolWrapper


class MockMCPClient:
    """Mock MCP client for testing."""

    def __init__(self):
        self.call_count = 0
        self.last_tool_name = None
        self.last_arguments = None

    async def call_tool(self, tool_name: str, arguments: dict):
        """Mock call_tool method."""
        self.call_count += 1
        self.last_tool_name = tool_name
        self.last_arguments = arguments

        # Return mock result
        class MockResult:
            class MockContent:
                text = "Mock tool output"

            content = [MockContent()]

        return MockResult()


@pytest.mark.asyncio
async def test_wrapper_initialization(sample_tool_def):
    """Test tool wrapper initialization."""
    client = MockMCPClient()
    wrapper = MCPToolWrapper("test-server", sample_tool_def, client)

    assert wrapper.server_name == "test-server"
    assert wrapper.tool_name == "test_tool"
    assert wrapper.name == "mcp_test-server_test_tool"
    assert wrapper.description == "A test tool"
    assert "properties" in wrapper.input_schema


@pytest.mark.asyncio
async def test_wrapper_execute(sample_tool_def):
    """Test tool execution through wrapper."""
    client = MockMCPClient()
    wrapper = MCPToolWrapper("test-server", sample_tool_def, client)

    # Execute tool
    result = await wrapper.execute({"input": "test"})

    # Verify execution
    assert result["success"] is True
    assert "Mock tool output" in result["output"]
    assert client.call_count == 1
    assert client.last_tool_name == "test_tool"
    assert client.last_arguments == {"input": "test"}


@pytest.mark.asyncio
async def test_wrapper_error_handling(sample_tool_def):
    """Test tool wrapper error handling."""

    class FailingClient:
        async def call_tool(self, tool_name: str, arguments: dict):
            raise RuntimeError("Tool execution failed")

    client = FailingClient()
    wrapper = MCPToolWrapper("test-server", sample_tool_def, client)

    # Execute tool (should handle error gracefully)
    result = await wrapper.execute({"input": "test"})

    assert result["success"] is False
    assert "Tool execution error" in result["output"]
