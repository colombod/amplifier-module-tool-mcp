"""Prompt wrapper that exposes MCP prompts as Amplifier Tools."""

import logging
from typing import Any

from amplifier_core import ToolResult

logger = logging.getLogger(__name__)


class MCPPromptWrapper:
    """
    Wraps an MCP server prompt as an Amplifier Tool.

    Prompts in MCP are reusable templates that can be filled with arguments.
    We wrap them as tools so they can be called by the LLM.
    """

    def __init__(self, server_name: str, prompt_def: dict[str, Any], client: Any):
        """
        Initialize prompt wrapper.

        Args:
            server_name: Name of the MCP server providing this prompt
            prompt_def: Prompt definition (name, description, arguments)
            client: MCPClient instance to use for prompt retrieval
        """
        self.server_name = server_name
        self.client = client

        # Extract prompt info
        self.prompt_name = prompt_def["name"]
        self._name = f"mcp_{server_name}_prompt_{self.prompt_name}"
        self._description = prompt_def.get("description", f"Get prompt: {self.prompt_name}")
        self.prompt_arguments = prompt_def.get("arguments", [])

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
        Input schema for the prompt tool.

        Builds schema from prompt's argument definitions.
        """
        properties = {}
        required = []

        for arg in self.prompt_arguments:
            properties[arg["name"]] = {
                "type": "string",  # MCP prompt args are typically strings
                "description": arg.get("description", ""),
            }
            if arg.get("required", False):
                required.append(arg["name"])

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        """
        Execute the prompt by retrieving it from the MCP server.

        Args:
            input: Tool input (prompt arguments)

        Returns:
            ToolResult with filled prompt messages
        """
        try:
            logger.info(f"Getting MCP prompt '{self.name}' with arguments: {input}")

            # Get prompt from MCP server
            result = await self.client.get_prompt(self.prompt_name, input)

            # Extract messages from result
            messages = self._extract_messages(result)

            logger.info(f"MCP prompt '{self.name}' retrieved successfully")

            return ToolResult(success=True, output=messages)

        except Exception as e:
            logger.error(f"MCP prompt '{self.name}' retrieval failed: {e}")
            return ToolResult(success=False, error={"message": str(e)})

    def _extract_messages(self, result: Any) -> str:
        """
        Extract messages from MCP prompt result.

        Args:
            result: Raw result from MCP server

        Returns:
            Formatted prompt messages
        """
        # Handle different result formats
        if hasattr(result, "messages"):
            # Result with messages attribute
            messages = result.messages
            if isinstance(messages, list):
                parts = []
                for msg in messages:
                    role = getattr(msg, "role", "unknown")
                    content = getattr(msg, "content", "")

                    # Handle content types
                    if hasattr(content, "text"):
                        text = content.text
                    elif isinstance(content, str):
                        text = content
                    else:
                        text = str(content)

                    parts.append(f"[{role}]\n{text}")

                return "\n\n".join(parts)
            return str(messages)

        # Fallback: convert to string
        return str(result)

    def __repr__(self) -> str:
        """String representation."""
        return f"MCPPromptWrapper(name={self.name}, server={self.server_name})"
