"""Tests for Streamable HTTP client."""

import pytest
from amplifier_module_tool_mcp.streamable_http_client import MCPStreamableHTTPClient


def test_streamable_http_client_initialization():
    """Test Streamable HTTP client initialization."""
    client = MCPStreamableHTTPClient(
        server_name="test-streamable",
        url="http://localhost:3000/mcp",
        headers={"X-Custom": "value"},
    )

    assert client.server_name == "test-streamable"
    assert client.url == "http://localhost:3000/mcp"
    assert client.headers == {"X-Custom": "value"}
    assert not client.is_connected
    assert client.tools == []
    assert client.resources == []
    assert client.prompts == []


def test_streamable_http_client_health_status():
    """Test Streamable HTTP client health status."""
    client = MCPStreamableHTTPClient(
        server_name="test-streamable",
        url="http://localhost:3000/mcp",
    )

    status = client.health_status

    assert status["server_name"] == "test-streamable"
    assert status["transport"] == "streamable-http"
    assert status["url"] == "http://localhost:3000/mcp"
    assert status["is_connected"] is False


def test_streamable_http_client_getters():
    """Test Streamable HTTP client getter methods."""
    client = MCPStreamableHTTPClient("test", "http://localhost:3000/mcp")

    # Initially empty
    assert client.get_tools() == []
    assert client.get_resources() == []
    assert client.get_prompts() == []


@pytest.mark.asyncio
async def test_streamable_http_client_disconnect_before_connect():
    """Test that disconnect works even if never connected."""
    client = MCPStreamableHTTPClient("test", "http://localhost:3000/mcp")

    # Should not crash
    await client.disconnect()

    assert not client.is_connected
