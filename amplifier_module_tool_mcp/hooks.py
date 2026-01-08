"""MCP visibility hook - makes available MCP servers and capabilities visible to agents."""

import logging
from typing import Any

from amplifier_core import HookResult

logger = logging.getLogger(__name__)


class MCPVisibilityHook:
    """Hook that injects available MCP servers and capabilities into context before each LLM call.
    
    This follows the skills module pattern of progressive disclosure:
    - Level 1 (Always visible): Server and capability metadata via this hook
    - Level 2 (On demand): Tool execution via standard tool calls
    """
    
    def __init__(self, manager: Any, config: dict[str, Any]):
        """Initialize hook with MCP manager.
        
        Args:
            manager: MCPManager instance with connected servers
            config: Hook configuration from visibility section
        """
        self.manager = manager
        self.enabled = config.get("enabled", True)
        self.inject_role = config.get("inject_role", "user")
        self.max_visible = config.get("max_servers_visible", 50)
        self.ephemeral = config.get("ephemeral", True)
        self.priority = config.get("priority", 20)
        
        logger.debug(
            f"Initialized MCPVisibilityHook: enabled={self.enabled}, "
            f"max_visible={self.max_visible}, ephemeral={self.ephemeral}"
        )
    
    async def on_provider_request(self, event: str, data: dict[str, Any]) -> HookResult:
        """Inject MCP servers list before LLM request.
        
        Event: provider:request (before each LLM call)
        
        Args:
            event: Event name (should be "provider:request")
            data: Event data dictionary
            
        Returns:
            HookResult with action="inject_context" if servers should be shown,
            or action="continue" if disabled or no servers available
        """
        if not self.enabled:
            return HookResult(action="continue")
        
        servers = self.manager.get_server_names()
        if not servers:
            return HookResult(action="continue")
        
        servers_text = self._format_servers_list()
        
        return HookResult(
            action="inject_context",
            context_injection=servers_text,
            context_injection_role=self.inject_role,
            ephemeral=self.ephemeral,
            suppress_output=True,
        )
    
    def _format_servers_list(self) -> str:
        """Format MCP servers and capabilities list as markdown.
        
        Returns:
            Formatted servers list string, or empty string if no servers
        """
        servers = self.manager.get_server_names()
        if not servers:
            return ""
        
        tools = self.manager.get_tools()
        resources = self.manager.get_resources()
        prompts = self.manager.get_prompts()
        
        lines = ["Available MCP servers and capabilities:"]
        lines.append("")
        
        # Group capabilities by server
        server_caps = {}
        for server_name in servers:
            server_tools = [name for name in tools.keys() if name.startswith(f"mcp_{server_name}_")]
            server_resources = [name for name in resources.keys() if name.startswith(f"mcp_{server_name}_")]
            server_prompts = [name for name in prompts.keys() if name.startswith(f"mcp_{server_name}_")]
            
            server_caps[server_name] = {
                "tools": len(server_tools),
                "resources": len(server_resources),
                "prompts": len(server_prompts)
            }
        
        # Sort and limit servers
        sorted_servers = sorted(servers)[:self.max_visible]
        
        for server_name in sorted_servers:
            caps = server_caps.get(server_name, {})
            caps_summary = []
            if caps.get("tools", 0) > 0:
                caps_summary.append(f"{caps['tools']} tools")
            if caps.get("resources", 0) > 0:
                caps_summary.append(f"{caps['resources']} resources")
            if caps.get("prompts", 0) > 0:
                caps_summary.append(f"{caps['prompts']} prompts")
            
            if caps_summary:
                lines.append(f"- **{server_name}**: {', '.join(caps_summary)}")
            else:
                lines.append(f"- **{server_name}**: no capabilities")
        
        # Show truncation if applicable
        if len(servers) > self.max_visible:
            remaining = len(servers) - self.max_visible
            lines.append("")
            lines.append(f"_(+{remaining} more servers)_")
        
        servers_content = "\n".join(lines)
        
        # Add behavioral note
        behavioral_note = (
            "\n\nThis context is for your reference only. DO NOT mention these MCP servers "
            "to the user unless they ask. Use the tools naturally when needed for tasks."
        )
        
        # Wrap in system-reminder tag with source attribution
        return f"<system-reminder source=\"hooks-mcp-visibility\">\n{servers_content}{behavioral_note}\n</system-reminder>"
