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
    source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main
    config:
      priority: 1
      default_model: claude-sonnet-4-5

# Or use OpenAI
#  - module: provider-openai
#    source: git+https://github.com/microsoft/amplifier-module-provider-openai@main
#    config:
#      priority: 1
#      default_model: gpt-4

# Add MCP tools
tools:
  - module: tool-mcp
    source: git+https://github.com/robotdad/amplifier-module-tool-mcp@main
    config:
      # Server output control (default: suppressed for clean UX)
      verbose_servers: false  # Set to true to see MCP server debug output
      server_log_dir: ~/.amplifier/logs/mcp-servers/  # Where server logs are saved when suppressed

      # Optional inline server config (overrides .amplifier/mcp.json)
      # servers:
      #   my-server:
      #     command: npx
      #     args: ["-y", "my-mcp-server"]

# Standard tools you'll want
  - module: tool-filesystem
    source: git+https://github.com/microsoft/amplifier-module-tool-filesystem@main
  - module: tool-bash
    source: git+https://github.com/microsoft/amplifier-module-tool-bash@main
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

### MCP Server Configuration

MCP servers are configured in `.amplifier/mcp.json` (see examples/mcp.json for examples).

The module will look for configuration in (priority order):
1. Inline config in this profile (see `servers:` section in config above)
2. Project `.amplifier/mcp.json`
3. User `~/.amplifier/mcp.json`
4. Environment variable `$AMPLIFIER_MCP_CONFIG`

### Server Output Control

By default, MCP server debug output is suppressed for clean UX. Server logs are saved to `~/.amplifier/logs/mcp-servers/` for troubleshooting.

**To see server output** (for debugging):

Option 1 - Profile config:
```yaml
tools:
  - module: tool-mcp
    config:
      verbose_servers: true
```

Option 2 - Environment variable:
```bash
AMPLIFIER_MCP_VERBOSE=true amplifier run --profile mcp-example "test"
```

**Server logs location** (when suppressed):
- Default: `~/.amplifier/logs/mcp-servers/{server-name}.log`
- Custom: Set `server_log_dir` in config

## Available MCP Servers

See examples/mcp.json for ready-to-use server configurations.
