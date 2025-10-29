"""Tool wrapper that exposes MCP tools as Amplifier Tools."""

import logging
from typing import Any

from amplifier_core import ToolResult

logger = logging.getLogger(__name__)


class MCPToolWrapper:
    """
    Wraps an MCP server tool as an Amplifier Tool.

    This adapter allows MCP tools to be used seamlessly in Amplifier's
    tool system. The wrapper handles:
    - Name prefixing to avoid conflicts
    - Input schema translation
    - Tool execution proxying to MCP server
    """

    def __init__(self, server_name: str, tool_def: dict[str, Any], client: Any, hooks: Any):
        """
        Initialize tool wrapper.

        Args:
            server_name: Name of the MCP server providing this tool
            tool_def: Tool definition from MCP server (name, description, input_schema)
            client: MCPClient instance to use for tool execution
            hooks: Hook registry for event emission (currently unused - orchestrator handles tool events)
        """
        self.server_name = server_name
        self.client = client
        self.hooks = hooks

        # Extract tool info
        self.tool_name = tool_def["name"]
        self._name = f"mcp_{server_name}_{self.tool_name}"
        self._description = tool_def.get("description", "")
        self._input_schema = tool_def.get("input_schema", {})

    @property
    def name(self) -> str:
        """Tool name."""
        return self._name

    @property
    def description(self) -> str:
        """Tool description."""
        return self._description

    @property
    def input_schema(self) -> dict[str, Any]:
        """Input schema for the tool."""
        return self._input_schema

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        """
        Execute the tool by proxying to the MCP server.

        Args:
            input: Tool input parameters

        Returns:
            ToolResult with success status and output/error

        Note:
            Tool execution events (TOOL_PRE, TOOL_POST, TOOL_ERROR) are emitted
            automatically by the orchestrator. No manual event emission needed here.
        """
        try:
            # Call tool on MCP server
            result = await self.client.call_tool(self.tool_name, input)

            # Extract content from result
            output = self._extract_content(result)

            return ToolResult(success=True, output=output)

        except Exception as e:
            logger.error(f"MCP tool '{self.name}' failed: {e}")
            return ToolResult(success=False, error={"message": str(e)})

    def _extract_content(self, result: Any) -> str:
        """
        Extract content from MCP tool result.

        Args:
            result: Raw result from MCP server

        Returns:
            String representation of the result
        """
        # Handle different result formats
        if hasattr(result, "content"):
            # Result with content attribute (standard MCP format)
            content_items = result.content
            if isinstance(content_items, list):
                # Join multiple content items
                return "\n".join(str(item.text) if hasattr(item, "text") else str(item) for item in content_items)
            return str(content_items)

        # Fallback: convert to string
        return str(result)

    def __repr__(self) -> str:
        """String representation."""
        return f"MCPToolWrapper(name={self.name}, server={self.server_name})"
