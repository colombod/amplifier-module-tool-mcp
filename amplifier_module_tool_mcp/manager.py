"""MCP Manager that orchestrates multiple MCP clients and their capabilities."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from amplifier_module_tool_mcp.client import MCPClient
from amplifier_module_tool_mcp.config import MCPConfig
from amplifier_module_tool_mcp.content_utils import DEFAULT_MAX_CONTENT_SIZE
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
    - Start/stop MCP clients (stdio and Streamable HTTP)
    - Discover tools, resources, and prompts from all servers
    - Create wrappers for all primitives
    - Provide unified registry for Amplifier
    """

    def __init__(self, config: dict[str, Any], coordinator: Any):
        """
        Initialize MCP manager.

        Args:
            config: Configuration dictionary (inline config from profile)
            coordinator: Amplifier coordinator instance for hooks
        """
        self.config = MCPConfig(config)
        self.coordinator = coordinator
        self.clients: dict[str, MCPClient | MCPStreamableHTTPClient] = {}
        self.tools: dict[str, MCPToolWrapper] = {}
        self.resources: dict[str, MCPResourceWrapper] = {}
        self.prompts: dict[str, MCPPromptWrapper] = {}

        # Verbose server output configuration
        # Default: suppress server stderr (quiet by default)
        # Can be overridden via config or environment variable
        self.verbose_servers = (
            config.get("verbose_servers", False)
            or os.environ.get("AMPLIFIER_MCP_VERBOSE", "").lower() in ("true", "1", "yes")
        )

        # Where to save server logs when suppressed
        default_log_dir = "~/.amplifier/logs/mcp-servers/"
        self.server_log_dir = Path(config.get("server_log_dir", default_log_dir)).expanduser()

        # Content size limit to prevent context exhaustion
        self.max_content_size = config.get("max_content_size", DEFAULT_MAX_CONTENT_SIZE)
        logger.debug(f"Content size limit: {self.max_content_size:,} characters")

    async def start(self) -> None:
        """
        Initialize MCP manager by loading configurations and creating clients.

        Lazy connection: Clients are created but NOT connected until first use.
        This prevents:
        - Slow servers from delaying startup
        - Connection errors from crashing initialization
        - Unnecessary connections to unused servers
        """
        logger.info("Initializing MCP manager...")

        # Load server configurations
        servers = self.config.load_servers()

        if not servers:
            logger.warning("No MCP servers configured - module will not provide any capabilities")
            return

        # Create client objects WITHOUT connecting
        for server_name, server_config in servers.items():
            try:
                self._create_client(server_name, server_config)
            except Exception as e:
                logger.error(f"Failed to create MCP client for '{server_name}': {e}")
                # Continue with other servers

        logger.info(f"MCP manager initialized with {len(self.clients)} server(s) (not yet connected)")

    def _create_client(self, server_name: str, server_config: dict[str, Any]) -> None:
        """
        Create a client for a server WITHOUT connecting.

        Args:
            server_name: Unique name for this server
            server_config: Server configuration
        """
        # Detect transport type
        transport_type = self._detect_transport_type(server_config)

        if transport_type == "streamable-http":
            self._create_streamable_http_client(server_name, server_config)
        elif transport_type == "stdio":
            self._create_stdio_client(server_name, server_config)
        else:
            logger.error(f"Unknown transport type '{transport_type}' for server '{server_name}'")

    def _detect_transport_type(self, server_config: dict[str, Any]) -> str:
        """
        Detect transport type from server configuration.

        Args:
            server_config: Server configuration

        Returns:
            "streamable-http" or "stdio"
        """
        # Explicit type in config
        if "type" in server_config:
            transport = server_config["type"]
            # Normalize variations
            if transport in ("streamable-http", "streamable_http", "streamablehttp", "http"):
                return "streamable-http"
            return transport

        # URL means Streamable HTTP (current spec)
        if "url" in server_config:
            return "streamable-http"

        # Command means stdio
        if "command" in server_config:
            return "stdio"

        # Default to stdio
        return "stdio"

    def _create_stdio_client(self, server_name: str, server_config: dict[str, Any]) -> None:
        """Create a stdio-based MCP client (without connecting)."""
        command = server_config.get("command")
        args = server_config.get("args", [])
        env = server_config.get("env", {})

        if not command:
            logger.error(f"Stdio server '{server_name}' missing 'command' in configuration")
            return

        # Substitute environment variables
        env = {k: MCPConfig.substitute_env_vars(v) for k, v in env.items()}

        # Create client WITHOUT connecting
        client = MCPClient(
            server_name, command, args, env, verbose_servers=self.verbose_servers, server_log_dir=self.server_log_dir
        )

        # Store client (not connected, no capabilities discovered yet)
        self.clients[server_name] = client
        logger.debug(f"Created stdio client for '{server_name}' (not yet connected)")

    def _create_streamable_http_client(self, server_name: str, server_config: dict[str, Any]) -> None:
        """Create a Streamable HTTP-based MCP client (without connecting)."""
        url = server_config.get("url")
        headers = server_config.get("headers", {})

        if not url:
            logger.error(f"Streamable HTTP server '{server_name}' missing 'url' in configuration")
            return

        # Substitute environment variables in headers
        headers = {k: MCPConfig.substitute_env_vars(v) for k, v in headers.items()}

        # Create client WITHOUT connecting
        client = MCPStreamableHTTPClient(server_name, url, headers)

        # Store client (not connected, no capabilities discovered yet)
        self.clients[server_name] = client
        logger.debug(f"Created streamable-http client for '{server_name}' (not yet connected)")

    async def _ensure_server_connected(self, server_name: str) -> None:
        """
        Ensure a server is connected and capabilities are discovered.

        This is called lazily when capabilities are first accessed.
        Handles connection and wrapper registration atomically.

        Args:
            server_name: Server to connect
        """
        client = self.clients.get(server_name)
        if not client:
            raise RuntimeError(f"Server '{server_name}' not found")

        # Check if already connected
        if client.is_connected:
            return

        # Connect and discover capabilities
        try:
            await client.connect()
            # Register wrappers for this server's capabilities
            await self._register_capabilities(server_name, client)
            logger.info(
                f"Lazily connected to '{server_name}': "
                f"{len(client.get_tools())} tools, "
                f"{len(client.get_resources())} resources, "
                f"{len(client.get_prompts())} prompts"
            )
        except (Exception, asyncio.CancelledError) as e:
            logger.error(f"Lazy connection failed for '{server_name}': {e}")
            # Don't re-raise - let caller decide whether to continue

    async def _register_capabilities(self, server_name: str, client: MCPClient | MCPStreamableHTTPClient) -> None:
        """
        Register all capabilities (tools, resources, prompts) from a client.

        Args:
            server_name: Server name
            client: Connected MCP client
        """
        # Register tools - pass hooks for event emission and content size limit
        for tool_def in client.get_tools():
            wrapper = MCPToolWrapper(
                server_name, tool_def, client, self.coordinator.hooks, max_content_size=self.max_content_size
            )
            self.tools[wrapper.name] = wrapper
            logger.debug(f"Registered tool '{wrapper.name}' from server '{server_name}'")

        # Register resources - pass hooks for event emission and content size limit
        for resource_def in client.get_resources():
            wrapper = MCPResourceWrapper(
                server_name, resource_def, client, self.coordinator.hooks, max_content_size=self.max_content_size
            )
            self.resources[wrapper.name] = wrapper
            logger.debug(f"Registered resource '{wrapper.name}' from server '{server_name}'")

        # Register prompts - pass hooks for event emission and content size limit
        for prompt_def in client.get_prompts():
            wrapper = MCPPromptWrapper(
                server_name, prompt_def, client, self.coordinator.hooks, max_content_size=self.max_content_size
            )
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

    async def get_tools(self) -> dict[str, MCPToolWrapper]:
        """
        Get all registered tools (connects lazily if needed).

        Returns:
            Dictionary of tool wrappers
        """
        # Ensure all servers are connected and wrappers registered
        for server_name in list(self.clients.keys()):
            try:
                await self._ensure_server_connected(server_name)
            except (Exception, asyncio.CancelledError) as e:
                logger.error(f"Failed to connect to '{server_name}' when listing tools: {e}")
                # Continue with other servers

        return self.tools

    async def get_resources(self) -> dict[str, MCPResourceWrapper]:
        """
        Get all registered resources (connects lazily if needed).

        Returns:
            Dictionary of resource wrappers
        """
        # Ensure all servers are connected and wrappers registered
        for server_name in list(self.clients.keys()):
            try:
                await self._ensure_server_connected(server_name)
            except (Exception, asyncio.CancelledError) as e:
                logger.error(f"Failed to connect to '{server_name}' when listing resources: {e}")
                # Continue with other servers

        return self.resources

    async def get_prompts(self) -> dict[str, MCPPromptWrapper]:
        """
        Get all registered prompts (connects lazily if needed).

        Returns:
            Dictionary of prompt wrappers
        """
        # Ensure all servers are connected and wrappers registered
        for server_name in list(self.clients.keys()):
            try:
                await self._ensure_server_connected(server_name)
            except (Exception, asyncio.CancelledError) as e:
                logger.error(f"Failed to connect to '{server_name}' when listing prompts: {e}")
                # Continue with other servers

        return self.prompts

    async def get_all_capabilities(self) -> dict[str, Any]:
        """
        Get all capabilities (connects lazily if needed).

        Returns:
            Dictionary with all wrappers
        """
        # Trigger lazy connection for all capability types
        await self.get_tools()
        await self.get_resources()
        await self.get_prompts()

        return {**self.tools, **self.resources, **self.prompts}

    def get_server_names(self) -> list[str]:
        """Get list of configured server names (not necessarily connected)."""
        return list(self.clients.keys())
