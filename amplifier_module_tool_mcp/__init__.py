"""
MCP (Model Context Protocol) Tool Module for Amplifier.

This module enables Amplifier to connect to MCP servers and expose their
capabilities (tools, resources, prompts) to LLM agents through the standard
Amplifier interface.
"""

# Amplifier module metadata
__amplifier_module_type__ = "tool"

import logging
from typing import Any

from amplifier_core import ModuleCoordinator

from amplifier_module_tool_mcp.manager import MCPManager

__version__ = "0.2.1"
__all__ = ["mount", "MCPManager"]

logger = logging.getLogger(__name__)


async def mount(coordinator: ModuleCoordinator, config: dict[str, Any] | None = None) -> None:
    """
    Mount the MCP tool module.

    This is the entry point called by Amplifier when loading this module.

    Args:
        coordinator: Amplifier coordinator instance
        config: Configuration dictionary with optional 'servers' key

    Returns:
        None

    Note:
        MCP connections use AsyncExitStack context managers that must be closed
        in the same async context they were created in. Therefore, we cannot
        return a cleanup function to be called later - the connections will be
        cleaned up when the process exits naturally.
    """
    manager = MCPManager(config or {}, coordinator)
    await manager.start()

    # Get all capabilities (this triggers lazy connection to all servers)
    capabilities = await manager.get_all_capabilities()

    # Register capabilities with the coordinator
    for cap_name, cap_wrapper in capabilities.items():
        await coordinator.mount("tools", cap_wrapper, name=cap_name)
        logger.debug(f"Mounted MCP capability: {cap_name}")

    # Log summary
    tools = await manager.get_tools()
    resources = await manager.get_resources()
    prompts = await manager.get_prompts()

    logger.info(
        f"MCP module mounted: {len(tools)} tools, {len(resources)} resources, "
        f"{len(prompts)} prompts from {len(manager.get_server_names())} servers"
    )
