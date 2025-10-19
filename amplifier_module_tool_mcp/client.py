"""MCP Client wrapper for connecting to and communicating with MCP servers."""

import logging
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """
    MCP client that manages connection to a single MCP server.

    Handles:
    - Server process lifecycle (start/stop)
    - Tool discovery via list_tools
    - Tool execution via call_tool
    - Basic error handling and reconnection

    The client maintains an active connection by managing the async context
    managers for the stdio transport and session.
    """

    def __init__(self, server_name: str, command: str, args: list[str], env: dict[str, str] | None = None):
        """
        Initialize MCP client.

        Args:
            server_name: Unique name for this server
            command: Command to execute (e.g., "npx", "python")
            args: Arguments for the command
            env: Optional environment variables
        """
        self.server_name = server_name
        self.command = command
        self.args = args
        self.env = env or {}
        self.session: ClientSession | None = None
        self.tools: list[dict[str, Any]] = []
        self._connected = False
        self._exit_stack: AsyncExitStack | None = None

    async def connect(self) -> None:
        """Connect to the MCP server and discover tools."""
        if self._connected:
            return

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

            self._connected = True
            logger.info(f"Connected to MCP server '{self.server_name}' - discovered {len(self.tools)} tools")

        except Exception as e:
            self._connected = False
            # Clean up on error
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None
            logger.error(f"Failed to connect to MCP server '{self.server_name}': {e}")
            raise RuntimeError(f"MCP server connection failed: {e}") from e

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        if not self._connected or not self.session:
            await self.connect()

        try:
            result = await self.session.call_tool(tool_name, arguments=arguments)
            return result

        except Exception as e:
            logger.error(f"Tool call failed for '{tool_name}' on '{self.server_name}': {e}")
            raise RuntimeError(f"Tool execution failed: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
                logger.info(f"Disconnected from MCP server '{self.server_name}'")
            except Exception as e:
                logger.error(f"Error disconnecting from '{self.server_name}': {e}")
            finally:
                self._exit_stack = None
                self.session = None
                self._connected = False

    def get_tools(self) -> list[dict[str, Any]]:
        """Get the list of discovered tools."""
        return self.tools
