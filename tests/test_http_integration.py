"""Integration tests for HTTP-based MCP servers."""

import pytest
from amplifier_module_tool_mcp.streamable_http_client import MCPStreamableHTTPClient


@pytest.mark.asyncio
async def test_deepwiki_streamable_http():
    """Test connection to deepwiki using Streamable HTTP transport."""
    client = MCPStreamableHTTPClient(
        server_name="deepwiki",
        url="https://mcp.deepwiki.com/mcp",
    )

    try:
        # Connect and discover
        await client.connect()

        # Verify connection
        assert client.is_connected
        assert client.session is not None

        # Verify tools discovered
        tools = client.get_tools()
        assert len(tools) >= 3  # Should have at least 3 tools

        # Check for expected deepwiki tools
        tool_names = [tool["name"] for tool in tools]
        assert "read_wiki_structure" in tool_names
        assert "read_wiki_contents" in tool_names
        assert "ask_question" in tool_names

        print(f"\n✅ deepwiki connected via Streamable HTTP - {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")

    finally:
        # Always disconnect
        await client.disconnect()
        assert not client.is_connected


@pytest.mark.asyncio
async def test_deepwiki_health_status():
    """Test health status reporting for HTTP client."""
    client = MCPStreamableHTTPClient(
        server_name="deepwiki",
        url="https://mcp.deepwiki.com/mcp",
    )

    # Check initial health
    status = client.health_status
    assert status["server_name"] == "deepwiki"
    assert status["transport"] == "streamable-http"
    assert status["url"] == "https://mcp.deepwiki.com/mcp"
    assert status["is_connected"] is False

    try:
        # Connect
        await client.connect()

        # Check connected health
        status = client.health_status
        assert status["is_connected"] is True
        assert status["tools_discovered"] >= 3

    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_streamable_http_capabilities_discovery():
    """Test that Streamable HTTP client discovers all capability types."""
    client = MCPStreamableHTTPClient(
        server_name="deepwiki",
        url="https://mcp.deepwiki.com/mcp",
    )

    try:
        await client.connect()

        # Should have methods for all capability types
        tools = client.get_tools()
        resources = client.get_resources()
        prompts = client.get_prompts()

        # deepwiki should have tools
        assert len(tools) > 0

        # May or may not have resources/prompts (depends on server)
        assert isinstance(resources, list)
        assert isinstance(prompts, list)

        print("\n✅ Capabilities discovered:")
        print(f"  Tools: {len(tools)}")
        print(f"  Resources: {len(resources)}")
        print(f"  Prompts: {len(prompts)}")

    finally:
        await client.disconnect()


# Note: wikidata tests commented out due to server returning 400 Bad Request
# This appears to be a server-side issue or authentication requirement

# @pytest.mark.asyncio
# async def test_wikidata_connection():
#     """Test connection to wikidata MCP server."""
#     client = MCPStreamableHTTPClient(
#         server_name="wikidata",
#         url="https://wd-mcp.wmcloud.org/mcp/",
#     )
#
#     try:
#         await client.connect()
#         tools = client.get_tools()
#         assert len(tools) > 0
#     finally:
#         await client.disconnect()
