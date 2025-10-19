"""MCP Manager that orchestrates multiple MCP clients and their capabilities."""

import logging
from typing import Any

from amplifier_module_tool_mcp.client import MCPClient
from amplifier_module_tool_mcp.config import MCPConfig
from amplifier_module_tool_mcp.http_client import MCPHTTPClient
from amplifier_module_tool_mcp.prompt_wrapper import MCPPromptWrapper
from amplifier_module_tool_mcp.resource_wrapper import MCPResourceWrapper
from amplifier_module_tool_mcp.streamable_http_client import MCPStreamableHTTPClient
from amplifier_module_tool_mcp.wrapper import MCPToolWrapper

logger = logging.getLogger(__name__)


class MCPManager:
    """
    Manages multiple MCP servers and their capabilities.

    Responsibilities:
    - Load server configurations
    - Start/stop MCP clients (stdio and HTTP)
    - Discover tools, resources, and prompts from all servers
    - Create wrappers for all primitives
    - Provide unified registry for Amplifier
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize MCP manager.

        Args:
            config: Configuration dictionary (inline config from profile)
        """
        self.config = MCPConfig(config)
        self.clients: dict[str, MCPClient | MCPHTTPClient] = {}
        self.tools: dict[str, MCPToolWrapper] = {}
        self.resources: dict[str, MCPResourceWrapper] = {}
        self.prompts: dict[str, MCPPromptWrapper] = {}

    async def start(self) -> None:
        """
        Start all configured MCP servers and discover their capabilities.

        This:
        1. Loads server configurations from all sources
        2. Creates MCP clients for each server (stdio or HTTP)
        3. Connects to servers and discovers capabilities
        4. Wraps tools, resources, and prompts for Amplifier
        """
        logger.info("Starting MCP manager...")

        # Load server configurations
        servers = self.config.load_servers()

        if not servers:
            logger.warning("No MCP servers configured - module will not provide any capabilities")
            return

        # Start each server
        for server_name, server_config in servers.items():
            try:
                await self._start_server(server_name, server_config)
            except Exception as e:
                logger.error(f"Failed to start MCP server '{server_name}': {e}")
                # Continue with other servers

        logger.info(
            f"MCP manager started: {len(self.tools)} tools, {len(self.resources)} resources, "
            f"{len(self.prompts)} prompts from {len(self.clients)} servers"
        )

    async def _start_server(self, server_name: str, server_config: dict[str, Any]) -> None:
        """
        Start a single MCP server and discover its capabilities.

        Args:
            server_name: Unique name for this server
            server_config: Server configuration
        """
        # Detect transport type
        transport_type = self._detect_transport_type(server_config)

        if transport_type == "http":
            await self._start_http_server(server_name, server_config)
        elif transport_type == "streamable-http":
            await self._start_streamable_http_server(server_name, server_config)
        elif transport_type == "stdio":
            await self._start_stdio_server(server_name, server_config)
        else:
            logger.error(f"Unknown transport type '{transport_type}' for server '{server_name}'")

    def _detect_transport_type(self, server_config: dict[str, Any]) -> str:
        """
        Detect transport type from server configuration.

        Args:
            server_config: Server configuration

        Returns:
            "http" or "stdio"
        """
        # Explicit type in config
        if "type" in server_config:
            return server_config["type"]

        # URL means HTTP
        if "url" in server_config:
            return "http"

        # Command means stdio
        if "command" in server_config:
            return "stdio"

        # Default to stdio
        return "stdio"

    async def _start_stdio_server(self, server_name: str, server_config: dict[str, Any]) -> None:
        """Start a stdio-based MCP server."""
        command = server_config.get("command")
        args = server_config.get("args", [])
        env = server_config.get("env", {})

        if not command:
            logger.error(f"Stdio server '{server_name}' missing 'command' in configuration")
            return

        # Substitute environment variables
        env = {k: MCPConfig.substitute_env_vars(v) for k, v in env.items()}

        # Create and connect client
        client = MCPClient(server_name, command, args, env)
        await client.connect()

        # Store client and register capabilities
        self.clients[server_name] = client
        await self._register_capabilities(server_name, client)

    async def _start_http_server(self, server_name: str, server_config: dict[str, Any]) -> None:
        """Start an HTTP/SSE-based MCP server."""
        url = server_config.get("url")
        headers = server_config.get("headers", {})

        if not url:
            logger.error(f"HTTP server '{server_name}' missing 'url' in configuration")
            return

        # Substitute environment variables in headers
        headers = {k: MCPConfig.substitute_env_vars(v) for k, v in headers.items()}

        # Create and connect client
        client = MCPHTTPClient(server_name, url, headers)
        await client.connect()

        # Store client and register capabilities
        self.clients[server_name] = client
        await self._register_capabilities(server_name, client)

    async def _start_streamable_http_server(self, server_name: str, server_config: dict[str, Any]) -> None:
        """Start a Streamable HTTP-based MCP server (2025-03-26 spec)."""
        url = server_config.get("url")
        headers = server_config.get("headers", {})

        if not url:
            logger.error(f"Streamable HTTP server '{server_name}' missing 'url' in configuration")
            return

        # Substitute environment variables in headers
        headers = {k: MCPConfig.substitute_env_vars(v) for k, v in headers.items()}

        # Create and connect client
        client = MCPStreamableHTTPClient(server_name, url, headers)
        await client.connect()

        # Store client and register capabilities
        self.clients[server_name] = client
        await self._register_capabilities(server_name, client)

    async def _register_capabilities(
        self, server_name: str, client: MCPClient | MCPHTTPClient | MCPStreamableHTTPClient
    ) -> None:
        """
        Register all capabilities (tools, resources, prompts) from a client.

        Args:
            server_name: Server name
            client: Connected MCP client
        """
        # Register tools
        for tool_def in client.get_tools():
            wrapper = MCPToolWrapper(server_name, tool_def, client)
            self.tools[wrapper.name] = wrapper
            logger.debug(f"Registered tool '{wrapper.name}' from server '{server_name}'")

        # Register resources
        for resource_def in client.get_resources():
            wrapper = MCPResourceWrapper(server_name, resource_def, client)
            self.resources[wrapper.name] = wrapper
            logger.debug(f"Registered resource '{wrapper.name}' from server '{server_name}'")

        # Register prompts
        for prompt_def in client.get_prompts():
            wrapper = MCPPromptWrapper(server_name, prompt_def, client)
            self.prompts[wrapper.name] = wrapper
            logger.debug(f"Registered prompt '{wrapper.name}' from server '{server_name}'")

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
        self.resources.clear()
        self.prompts.clear()

        logger.info("MCP manager stopped")

    def get_tools(self) -> dict[str, MCPToolWrapper]:
        """Get all registered tools."""
        return self.tools

    def get_resources(self) -> dict[str, MCPResourceWrapper]:
        """Get all registered resources."""
        return self.resources

    def get_prompts(self) -> dict[str, MCPPromptWrapper]:
        """Get all registered prompts."""
        return self.prompts

    def get_all_capabilities(self) -> dict[str, Any]:
        """
        Get all capabilities (tools + resources + prompts).

        Returns:
            Dictionary with all wrappers
        """
        return {**self.tools, **self.resources, **self.prompts}

    def get_server_names(self) -> list[str]:
        """Get list of connected server names."""
        return list(self.clients.keys())
