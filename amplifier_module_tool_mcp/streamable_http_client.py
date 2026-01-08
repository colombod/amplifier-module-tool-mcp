"""Streamable HTTP transport MCP client (2025-03-26 spec)."""

import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from amplifier_module_tool_mcp.reconnection import CircuitBreaker
from amplifier_module_tool_mcp.reconnection import ReconnectionConfig
from amplifier_module_tool_mcp.reconnection import ReconnectionStrategy

logger = logging.getLogger(__name__)


class MCPStreamableHTTPClient:
    """
    MCP client using Streamable HTTP transport (2025-03-26 spec).

    This is the newer HTTP transport that replaces HTTP+SSE in the
    latest MCP specification. It uses a single endpoint for both
    POST and GET requests with optional SSE streaming.
    """

    def __init__(
        self,
        server_name: str,
        url: str,
        headers: dict[str, str] | None = None,
        reconnection_config: ReconnectionConfig | None = None,
    ):
        """
        Initialize Streamable HTTP MCP client.

        Args:
            server_name: Unique name for this server
            url: HTTP endpoint URL
            headers: Optional HTTP headers
            reconnection_config: Reconnection configuration
        """
        self.server_name = server_name
        self.url = url
        self.headers = headers or {}
        self.session: ClientSession | None = None
        self.tools: list[dict[str, Any]] = []
        self.resources: list[dict[str, Any]] = []
        self.prompts: list[dict[str, Any]] = []
        self._connected = False
        self._exit_stack: AsyncExitStack | None = None

        # Reconnection and health management
        self._reconnection_strategy = ReconnectionStrategy(reconnection_config)
        self._circuit_breaker = CircuitBreaker()
        self._connection_attempts = 0
        self._last_error: Exception | None = None

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected

    @property
    def health_status(self) -> dict[str, Any]:
        """Get health status of the connection."""
        return {
            "server_name": self.server_name,
            "transport": "streamable-http",
            "url": self.url,
            "is_connected": self.is_connected,
            "circuit_breaker_state": self._circuit_breaker.state,
            "connection_attempts": self._connection_attempts,
            "tools_discovered": len(self.tools),
            "resources_discovered": len(self.resources),
            "prompts_discovered": len(self.prompts),
            "last_error": str(self._last_error) if self._last_error else None,
        }

    async def connect(self) -> None:
        """Connect to the Streamable HTTP MCP server and discover capabilities."""
        if self._connected:
            return

        # Check circuit breaker
        if self._circuit_breaker.is_open():
            logger.warning(f"Circuit breaker is OPEN for '{self.server_name}' - blocking connection attempt")
            raise RuntimeError(f"Circuit breaker is OPEN for server '{self.server_name}'")

        self._connection_attempts += 1

        try:
            # Use AsyncExitStack to manage context managers
            self._exit_stack = AsyncExitStack()

            # Connect via Streamable HTTP
            # Note: Returns (read, write, get_session_id) unlike other transports
            read, write, get_session_id = await self._exit_stack.enter_async_context(
                streamablehttp_client(self.url, headers=self.headers)
            )

            # Store session ID getter for resumability
            self._get_session_id = get_session_id

            # Create session
            session = await self._exit_stack.enter_async_context(ClientSession(read, write))

            # Initialize
            await session.initialize()
            self.session = session

            # Discover capabilities
            await self._discover_capabilities()

            self._connected = True
            self._circuit_breaker.record_success()
            self._last_error = None

            logger.info(
                f"Connected to Streamable HTTP MCP server '{self.server_name}' at {self.url} - "
                f"discovered {len(self.tools)} tools, {len(self.resources)} resources, "
                f"{len(self.prompts)} prompts"
            )

        except Exception as e:
            self._connected = False
            self._last_error = e
            self._circuit_breaker.record_failure()

            # Clean up on error - just drop references, no async cleanup
            self._exit_stack = None  # Don't call aclose() - just drop reference

            logger.error(f"Failed to connect to Streamable HTTP MCP server '{self.server_name}': {e}")
            raise RuntimeError(f"Streamable HTTP MCP server connection failed: {e}") from e

    async def _discover_capabilities(self) -> None:
        """Discover tools, resources, and prompts from server."""
        if not self.session:
            return

        # Discover tools
        tools_result = await self.session.list_tools()
        self.tools = [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in tools_result.tools
        ]

        # Discover resources
        try:
            resources_result = await self.session.list_resources()
            self.resources = [
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description or "",
                    "mime_type": resource.mimeType if hasattr(resource, "mimeType") else None,
                }
                for resource in resources_result.resources
            ]
        except Exception as e:
            logger.debug(f"Server '{self.server_name}' does not support resources: {e}")
            self.resources = []

        # Discover prompts
        try:
            prompts_result = await self.session.list_prompts()
            self.prompts = [
                {
                    "name": prompt.name,
                    "description": prompt.description or "",
                    "arguments": [
                        {"name": arg.name, "description": arg.description or "", "required": arg.required}
                        for arg in (prompt.arguments or [])
                    ],
                }
                for prompt in prompts_result.prompts
            ]
        except Exception as e:
            logger.debug(f"Server '{self.server_name}' does not support prompts: {e}")
            self.prompts = []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        if not self._connected or not self.session:
            await self.connect()

        try:
            result = await self.session.call_tool(tool_name, arguments=arguments)
            self._circuit_breaker.record_success()
            return result

        except Exception as e:
            self._circuit_breaker.record_failure()
            self._last_error = e
            logger.error(f"Tool call failed for '{tool_name}' on '{self.server_name}': {e}")
            raise RuntimeError(f"Tool execution failed: {e}") from e

    async def read_resource(self, uri: str) -> Any:
        """Read a resource from the MCP server."""
        if not self._connected or not self.session:
            await self.connect()

        try:
            result = await self.session.read_resource(uri=uri)
            self._circuit_breaker.record_success()
            return result

        except Exception as e:
            self._circuit_breaker.record_failure()
            self._last_error = e
            logger.error(f"Resource read failed for '{uri}' on '{self.server_name}': {e}")
            raise RuntimeError(f"Resource read failed: {e}") from e

    async def get_prompt(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Get a prompt from the MCP server."""
        if not self._connected or not self.session:
            await self.connect()

        try:
            result = await self.session.get_prompt(name=name, arguments=arguments or {})
            self._circuit_breaker.record_success()
            return result

        except Exception as e:
            self._circuit_breaker.record_failure()
            self._last_error = e
            logger.error(f"Get prompt failed for '{name}' on '{self.server_name}': {e}")
            raise RuntimeError(f"Get prompt failed: {e}") from e

    async def set_logging_level(self, level: str) -> None:
        """Set the logging level for the MCP server."""
        if not self._connected or not self.session:
            await self.connect()

        try:
            await self.session.set_logging_level(level=level)
            logger.info(f"Set logging level to '{level}' for server '{self.server_name}'")

        except Exception as e:
            logger.error(f"Failed to set logging level: {e}")
            raise

    async def disconnect(self) -> None:
        """
        Disconnect from the Streamable HTTP MCP server.

        NOTE: This method updates state flags but does NOT perform async cleanup.
        Cleanup is handled automatically when the process exits. Explicit async
        cleanup across task boundaries causes AsyncExitStack errors with anyio
        cancel scopes.
        
        The AsyncExitStack, ClientSession, and HTTP connections will all be
        cleaned up naturally when the process terminates.
        """
        if not self._connected:
            return

        # Update state flags for API consistency, but skip async cleanup
        self._connected = False
        self.session = None
        self._exit_stack = None  # Don't call aclose() - just drop reference
        
        logger.debug(f"Marked '{self.server_name}' as disconnected (cleanup on process exit)")

    def get_tools(self) -> list[dict[str, Any]]:
        """Get the list of discovered tools."""
        return self.tools

    def get_resources(self) -> list[dict[str, Any]]:
        """Get the list of discovered resources."""
        return self.resources

    def get_prompts(self) -> list[dict[str, Any]]:
        """Get the list of discovered prompts."""
        return self.prompts
