"""
MCP (Model Context Protocol) Tool Module for Amplifier.

This module enables Amplifier to connect to MCP servers and expose their
capabilities (tools, resources, prompts) to LLM agents through the standard
Amplifier interface.
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
    manager = MCPManager(config or {}, coordinator)
    await manager.start()

    # Register all capabilities with the coordinator
    capabilities = manager.get_all_capabilities()

    for cap_name, cap_wrapper in capabilities.items():
        await coordinator.mount("tools", cap_wrapper, name=cap_name)
        logger.debug(f"Mounted MCP capability: {cap_name}")

    # Log summary
    tools = manager.get_tools()
    resources = manager.get_resources()
    prompts = manager.get_prompts()

    logger.info(
        f"MCP module mounted: {len(tools)} tools, {len(resources)} resources, "
        f"{len(prompts)} prompts from {len(manager.get_server_names())} servers"
    )

    # Return cleanup function
    async def cleanup():
        logger.info("Cleaning up MCP module...")
        await manager.stop()

    return cleanup
