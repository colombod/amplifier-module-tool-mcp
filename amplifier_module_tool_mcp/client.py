"""MCP Client wrapper for connecting to and communicating with MCP servers."""

import logging
from contextlib import AsyncExitStack
from enum import Enum
from typing import Any

from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

from amplifier_module_tool_mcp.reconnection import CircuitBreaker
from amplifier_module_tool_mcp.reconnection import ReconnectionConfig
from amplifier_module_tool_mcp.reconnection import ReconnectionStrategy

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection state enumeration."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"


class MCPClient:
    """
    MCP client that manages connection to a single MCP server.

    Handles:
    - Server process lifecycle (start/stop)
    - Tool discovery via list_tools
    - Tool execution via call_tool
    - Reconnection with exponential backoff
    - Circuit breaker for failing servers
    - Health monitoring

    The client maintains an active connection by managing the async context
    managers for the stdio transport and session.
    """

    def __init__(
        self,
        server_name: str,
        command: str,
        args: list[str],
        env: dict[str, str] | None = None,
        reconnection_config: ReconnectionConfig | None = None,
    ):
        """
        Initialize MCP client.

        Args:
            server_name: Unique name for this server
            command: Command to execute (e.g., "npx", "python")
            args: Arguments for the command
            env: Optional environment variables
            reconnection_config: Reconnection configuration (uses defaults if None)
        """
        self.server_name = server_name
        self.command = command
        self.args = args
        self.env = env or {}
        self.session: ClientSession | None = None
        self.tools: list[dict[str, Any]] = []
        self._state = ConnectionState.DISCONNECTED
        self._exit_stack: AsyncExitStack | None = None

        # Reconnection and health management
        self._reconnection_strategy = ReconnectionStrategy(reconnection_config)
        self._circuit_breaker = CircuitBreaker()
        self._connection_attempts = 0
        self._last_error: Exception | None = None

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._state == ConnectionState.CONNECTED

    @property
    def health_status(self) -> dict[str, Any]:
        """
        Get health status of the connection.

        Returns:
            Dictionary with health information
        """
        return {
            "server_name": self.server_name,
            "state": self._state.value,
            "is_connected": self.is_connected,
            "circuit_breaker_state": self._circuit_breaker.state,
            "connection_attempts": self._connection_attempts,
            "tools_discovered": len(self.tools),
            "last_error": str(self._last_error) if self._last_error else None,
        }

    async def connect(self) -> None:
        """Connect to the MCP server and discover tools."""
        if self.is_connected:
            return

        # Check circuit breaker
        if self._circuit_breaker.is_open():
            logger.warning(f"Circuit breaker is OPEN for '{self.server_name}' - blocking connection attempt")
            raise RuntimeError(f"Circuit breaker is OPEN for server '{self.server_name}' - too many recent failures")

        self._state = ConnectionState.CONNECTING
        self._connection_attempts += 1

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env if self.env else None,
            )

            # Use AsyncExitStack to manage context managers and keep connection alive
            self._exit_stack = AsyncExitStack()

            # Enter stdio_client context
            read, write = await self._exit_stack.enter_async_context(stdio_client(server_params))

            # Enter ClientSession context
            session = await self._exit_stack.enter_async_context(ClientSession(read, write))

            # Initialize the session
            await session.initialize()

            # Store session
            self.session = session

            # Discover tools
            result = await session.list_tools()
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema,
                }
                for tool in result.tools
            ]

            self._state = ConnectionState.CONNECTED
            self._circuit_breaker.record_success()
            self._last_error = None

            logger.info(f"Connected to MCP server '{self.server_name}' - discovered {len(self.tools)} tools")

        except Exception as e:
            self._state = ConnectionState.ERROR
            self._last_error = e
            self._circuit_breaker.record_failure()

            # Clean up on error
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None

            logger.error(f"Failed to connect to MCP server '{self.server_name}': {e}")
            raise RuntimeError(f"MCP server connection failed: {e}") from e

    async def connect_with_retry(self) -> None:
        """Connect with automatic retry on failure."""

        async def _connect() -> None:
            await self.connect()

        await self._reconnection_strategy.execute_with_retry(_connect, f"connect to {self.server_name}")

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        if not self.is_connected or not self.session:
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

    async def call_tool_with_retry(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        Call a tool with automatic retry on failure.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result
        """

        async def _call() -> Any:
            return await self.call_tool(tool_name, arguments)

        return await self._reconnection_strategy.execute_with_retry(
            _call, f"call tool {tool_name} on {self.server_name}"
        )

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._state == ConnectionState.DISCONNECTED:
            return

        self._state = ConnectionState.DISCONNECTING

        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
                logger.info(f"Disconnected from MCP server '{self.server_name}'")
            except Exception as e:
                logger.error(f"Error disconnecting from '{self.server_name}': {e}")
            finally:
                self._exit_stack = None
                self.session = None

        self._state = ConnectionState.DISCONNECTED

    async def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker (useful for manual recovery)."""
        self._circuit_breaker.reset()
        logger.info(f"Circuit breaker reset for '{self.server_name}'")

    def get_tools(self) -> list[dict[str, Any]]:
        """Get the list of discovered tools."""
        return self.tools
