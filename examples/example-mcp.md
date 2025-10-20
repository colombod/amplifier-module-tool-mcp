---
profile:
  name: example-mcp
  version: "1.0.0"
  description: "Example profile with MCP tools enabled"
  extends: base

session:
  orchestrator:
    module: loop-basic
  context:
    module: context-simple

# Use your preferred provider
providers:
  - module: provider-anthropic
    config:
      priority: 1
      default_model: claude-sonnet-4-5

# Or use OpenAI
#  - module: provider-openai
#    config:
#      priority: 1
#      default_model: gpt-4

# Add MCP tools
tools:
  - module: tool-mcp
    # Optional inline config (overrides .amplifier/mcp.json)
    # config:
    #   servers:
    #     my-server:
    #       command: npx
    #       args: ["-y", "my-mcp-server"]

# Standard tools you'll want
  - module: tool-filesystem
  - module: tool-bash
---

# Example Profile with MCP Tools

This profile demonstrates how to enable MCP (Model Context Protocol) tools in Amplifier.

## What This Enables

When you use this profile, your LLM agent gets access to tools from configured MCP servers:
- Code analysis tools (repomix)
- Documentation search (context7)
- Browser automation (browser-use)
- AI workflows (zen)
- And any other MCP servers you configure

## Quick Start

1. Copy this file to your project:
   ```bash
   cp examples/example-mcp.md .amplifier/profiles/
   ```

2. Create MCP server configuration (see examples/mcp.json):
   ```bash
   cp examples/mcp.json .amplifier/
   ```

3. Use the profile:
   ```bash
   amplifier run --profile example-mcp "What MCP tools do you have?"
   ```

## Configuration

MCP servers are configured in `.amplifier/mcp.json` (see examples/mcp.json for examples).

The module will look for configuration in (priority order):
1. Inline config in this profile (uncomment the config section above)
2. Project `.amplifier/mcp.json`
3. User `~/.amplifier/mcp.json`
4. Environment variable `$AMPLIFIER_MCP_CONFIG`

## Available MCP Servers

See examples/mcp.json for ready-to-use server configurations.
