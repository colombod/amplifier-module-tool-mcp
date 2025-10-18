"""MCP Manager that orchestrates multiple MCP clients and their tools."""

import logging
from typing import Any

from amplifier_module_tool_mcp.client import MCPClient
from amplifier_module_tool_mcp.config import MCPConfig
from amplifier_module_tool_mcp.wrapper import MCPToolWrapper

logger = logging.getLogger(__name__)


class MCPManager:
    """
    Manages multiple MCP servers and their tools.

    Responsibilities:
    - Load server configurations
    - Start/stop MCP clients
    - Discover tools from all servers
    - Create tool wrappers
    - Provide unified tool registry
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize MCP manager.

        Args:
            config: Configuration dictionary (inline config from profile)
        """
        self.config = MCPConfig(config)
        self.clients: dict[str, MCPClient] = {}
        self.tools: dict[str, MCPToolWrapper] = {}

    async def start(self) -> None:
        """
        Start all configured MCP servers and discover their tools.

        This:
        1. Loads server configurations from all sources
        2. Creates MCP clients for each server
        3. Connects to servers and discovers tools
        4. Wraps tools in Amplifier Tool interface
        """
        logger.info("Starting MCP manager...")

        # Load server configurations
        servers = self.config.load_servers()

        if not servers:
            logger.warning("No MCP servers configured - module will not provide any tools")
            return

        # Start each server
        for server_name, server_config in servers.items():
            try:
                await self._start_server(server_name, server_config)
            except Exception as e:
                logger.error(f"Failed to start MCP server '{server_name}': {e}")
                # Continue with other servers

        logger.info(f"MCP manager started with {len(self.tools)} total tools from {len(self.clients)} servers")

    async def _start_server(self, server_name: str, server_config: dict[str, Any]) -> None:
        """
        Start a single MCP server and discover its tools.

        Args:
            server_name: Unique name for this server
            server_config: Server configuration (command, args, env)
        """
        # Extract configuration
        command = server_config.get("command")
        args = server_config.get("args", [])
        env = server_config.get("env", {})

        if not command:
            logger.error(f"Server '{server_name}' missing 'command' in configuration")
            return

        # Substitute environment variables in config
        env = {k: MCPConfig.substitute_env_vars(v) for k, v in env.items()}

        # Create and connect client
        client = MCPClient(server_name, command, args, env)
        await client.connect()

        # Store client
        self.clients[server_name] = client

        # Wrap and register tools
        for tool_def in client.get_tools():
            wrapper = MCPToolWrapper(server_name, tool_def, client)
            self.tools[wrapper.name] = wrapper
            logger.debug(f"Registered tool '{wrapper.name}' from server '{server_name}'")

    async def stop(self) -> None:
        """Stop all MCP servers."""
        logger.info("Stopping MCP manager...")

        for server_name, client in self.clients.items():
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from server '{server_name}': {e}")

        self.clients.clear()
        self.tools.clear()

        logger.info("MCP manager stopped")

    def get_tools(self) -> dict[str, MCPToolWrapper]:
        """
        Get all registered tools.

        Returns:
            Dictionary mapping tool names to tool wrapper instances
        """
        return self.tools

    def get_server_names(self) -> list[str]:
        """Get list of connected server names."""
        return list(self.clients.keys())
