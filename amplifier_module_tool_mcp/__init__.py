"""
MCP (Model Context Protocol) Tool Module for Amplifier.

This module enables Amplifier to connect to MCP servers and expose their tools
to LLM agents through the standard Amplifier Tool interface.
"""

import logging

from amplifier_core import ModuleCoordinator

from amplifier_module_tool_mcp.manager import MCPManager

__version__ = "0.1.0"
__all__ = ["mount", "MCPManager"]

logger = logging.getLogger(__name__)


async def mount(coordinator: ModuleCoordinator, config: dict | None = None):
    """
    Mount the MCP tool module.

    This is the entry point called by Amplifier when loading this module.

    Args:
        coordinator: Amplifier coordinator instance
        config: Configuration dictionary with optional 'servers' key

    Returns:
        Optional cleanup function
    """
    manager = MCPManager(config or {})
    await manager.start()

    # Register each discovered tool with the coordinator
    tools = manager.get_tools()
    for tool_name, tool in tools.items():
        await coordinator.mount("tools", tool, name=tool_name)
        logger.info(f"Mounted MCP tool: {tool_name}")

    logger.info(f"MCP module mounted with {len(tools)} tools from {len(manager.get_server_names())} servers")

    # Return cleanup function
    async def cleanup():
        logger.info("Cleaning up MCP module...")
        await manager.stop()

    return cleanup
