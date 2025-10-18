"""
MCP (Model Context Protocol) Tool Module for Amplifier.

This module enables Amplifier to connect to MCP servers and expose their tools
to LLM agents through the standard Amplifier Tool interface.
"""

from amplifier_module_tool_mcp.manager import MCPManager

__version__ = "0.1.0"
__all__ = ["mount", "MCPManager"]


async def mount(config: dict | None = None) -> dict[str, object]:
    """
    Mount the MCP tool module.

    This is the entry point called by Amplifier when loading this module.

    Args:
        config: Configuration dictionary with optional 'servers' key

    Returns:
        Dictionary mapping tool names to Tool instances
    """
    manager = MCPManager(config or {})
    await manager.start()
    return manager.get_tools()
