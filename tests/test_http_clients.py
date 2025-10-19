"""Tests for HTTP and Streamable HTTP clients."""

import pytest
from amplifier_module_tool_mcp.http_client import MCPHTTPClient
from amplifier_module_tool_mcp.streamable_http_client import MCPStreamableHTTPClient


def test_http_client_initialization():
    """Test HTTP client initialization."""
    client = MCPHTTPClient(
        server_name="test-http",
        url="http://localhost:3000/mcp",
        headers={"Authorization": "Bearer test"},
    )

    assert client.server_name == "test-http"
    assert client.url == "http://localhost:3000/mcp"
    assert client.headers == {"Authorization": "Bearer test"}
    assert not client.is_connected
    assert client.tools == []
    assert client.resources == []
    assert client.prompts == []


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


def test_http_client_health_status():
    """Test HTTP client health status."""
    client = MCPHTTPClient(
        server_name="test-http",
        url="http://localhost:3000/mcp",
    )

    status = client.health_status

    assert status["server_name"] == "test-http"
    assert status["transport"] == "http/sse"
    assert status["url"] == "http://localhost:3000/mcp"
    assert status["is_connected"] is False
    assert "circuit_breaker_state" in status
    assert "tools_discovered" in status
    assert "resources_discovered" in status
    assert "prompts_discovered" in status


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


def test_http_client_getters():
    """Test HTTP client getter methods."""
    client = MCPHTTPClient("test", "http://localhost:3000/mcp")

    # Initially empty
    assert client.get_tools() == []
    assert client.get_resources() == []
    assert client.get_prompts() == []


def test_streamable_http_client_getters():
    """Test Streamable HTTP client getter methods."""
    client = MCPStreamableHTTPClient("test", "http://localhost:3000/mcp")

    # Initially empty
    assert client.get_tools() == []
    assert client.get_resources() == []
    assert client.get_prompts() == []


# Note: Integration tests with real HTTP servers would require
# a running MCP server, which is environment-dependent.
# These tests validate the client structure and API.


@pytest.mark.asyncio
async def test_http_client_disconnect_before_connect():
    """Test that disconnect works even if never connected."""
    client = MCPHTTPClient("test", "http://localhost:3000/mcp")

    # Should not crash
    await client.disconnect()

    assert not client.is_connected


@pytest.mark.asyncio
async def test_streamable_http_client_disconnect_before_connect():
    """Test that disconnect works even if never connected."""
    client = MCPStreamableHTTPClient("test", "http://localhost:3000/mcp")

    # Should not crash
    await client.disconnect()

    assert not client.is_connected
