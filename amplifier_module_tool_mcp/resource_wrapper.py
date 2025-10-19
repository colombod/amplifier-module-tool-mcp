"""Resource wrapper that exposes MCP resources as Amplifier Tools."""

import logging
from typing import Any

from amplifier_core import ToolResult

logger = logging.getLogger(__name__)


class MCPResourceWrapper:
    """
    Wraps an MCP server resource as an Amplifier Tool.

    Resources in MCP are files, data, or URIs that servers expose.
    We wrap them as tools so they can be called by the LLM.
    """

    def __init__(self, server_name: str, resource_def: dict[str, Any], client: Any):
        """
        Initialize resource wrapper.

        Args:
            server_name: Name of the MCP server providing this resource
            resource_def: Resource definition (uri, name, description, mime_type)
            client: MCPClient instance to use for resource reading
        """
        self.server_name = server_name
        self.client = client

        # Extract resource info
        self.resource_uri = resource_def["uri"]
        resource_name_clean = resource_def["name"].replace("/", "_").replace(":", "_")
        self._name = f"mcp_{server_name}_resource_{resource_name_clean}"
        self._description = resource_def.get("description", f"Read resource: {resource_def['name']}")
        self.mime_type = resource_def.get("mime_type")

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
        """
        Input schema for the resource tool.

        Resources are read-only, so no parameters needed beyond
        optional overrides.
        """
        return {
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": f"Resource URI (default: {self.resource_uri})",
                    "default": self.resource_uri,
                }
            },
            "required": [],
        }

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        """
        Execute the resource read by proxying to the MCP server.

        Args:
            input: Tool input (optional uri override)

        Returns:
            ToolResult with resource content
        """
        try:
            # Use provided URI or default to resource's URI
            uri = input.get("uri", self.resource_uri)

            logger.info(f"Reading MCP resource '{self.name}' (uri: {uri})")

            # Read resource from MCP server
            result = await self.client.read_resource(uri)

            # Extract content from result
            content = self._extract_content(result)

            logger.info(f"MCP resource '{self.name}' read successfully")

            return ToolResult(success=True, output=content)

        except Exception as e:
            logger.error(f"MCP resource '{self.name}' read failed: {e}")
            return ToolResult(success=False, error={"message": str(e)})

    def _extract_content(self, result: Any) -> str:
        """
        Extract content from MCP resource result.

        Args:
            result: Raw result from MCP server

        Returns:
            String representation of the resource content
        """
        # Handle different result formats
        if hasattr(result, "contents"):
            # Result with contents attribute (standard MCP format)
            content_items = result.contents
            if isinstance(content_items, list):
                # Join multiple content items
                parts = []
                for item in content_items:
                    if hasattr(item, "text"):
                        parts.append(item.text)
                    elif hasattr(item, "blob"):
                        parts.append(f"[Binary content: {len(item.blob)} bytes]")
                    else:
                        parts.append(str(item))
                return "\n".join(parts)
            return str(content_items)

        # Fallback: convert to string
        return str(result)

    def __repr__(self) -> str:
        """String representation."""
        return f"MCPResourceWrapper(name={self.name}, server={self.server_name}, uri={self.resource_uri})"
