---
bundle:
  name: mcp-example
  version: 1.0.0
  description: Example bundle demonstrating MCP integration with Amplifier

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/robotdad/amplifier-module-tool-mcp@main#subdirectory=behaviors/mcp.yaml
---

# Example Bundle with MCP Tools

This bundle demonstrates how to enable MCP (Model Context Protocol) tools in Amplifier.

## What This Enables

When you use this bundle, your LLM agent gets access to tools from configured MCP servers:
- Database operations (postgres, sqlite)
- Web automation (puppeteer)
- Web search (brave-search)
- And any other MCP servers you configure

## Quick Start

### 1. Create this bundle file

Save this as `.amplifier/bundles/mcp-example.md` or any location you prefer.

### 2. Create MCP server configuration

Create `.amplifier/mcp.json`:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "${DATABASE_URL}"
      }
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

### 3. Use the bundle

```bash
amplifier bundle use .amplifier/bundles/mcp-example.md
amplifier run "What MCP tools are available?"
```

## Configuration

### MCP Server Configuration

MCP servers are configured in `.amplifier/mcp.json`.

The module will look for configuration in (priority order):
1. Inline config in your bundle (see behavior config section)
2. Project `.amplifier/mcp.json`
3. User `~/.amplifier/mcp.json`
4. Environment variable `$AMPLIFIER_MCP_CONFIG`

### Server Output Control

By default, MCP server debug output is suppressed for clean UX. Server logs are saved to `~/.amplifier/logs/mcp-servers/` for troubleshooting.

**To see server output** (for debugging):

Environment variable:
```bash
AMPLIFIER_MCP_VERBOSE=true amplifier run "test"
```

**Server logs location** (when suppressed):
- Default: `~/.amplifier/logs/mcp-servers/{server-name}.log`

## Popular MCP Servers

- `@modelcontextprotocol/server-postgres` - PostgreSQL database operations
- `@modelcontextprotocol/server-puppeteer` - Web automation and scraping
- `@modelcontextprotocol/server-sqlite` - SQLite database operations
- `@modelcontextprotocol/server-brave-search` - Web search via Brave API

See [MCP Server Registry](https://github.com/modelcontextprotocol/servers) for more.

**Note:** Amplifier's built-in filesystem and bash tools are recommended for file operations and shell commands.

## Customizing Configuration

To override the default MCP behavior configuration, create your own bundle with custom settings:

```yaml
---
bundle:
  name: my-custom-mcp
  version: 1.0.0

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

tools:
  - module: tool-mcp
    source: git+https://github.com/robotdad/amplifier-module-tool-mcp@main
    config:
      verbose_servers: true  # Show server debug output
      max_content_size: 100000  # Allow larger responses
      servers:
        # Inline server config (optional)
        my-server:
          command: npx
          args: ["-y", "my-mcp-server"]
---

# Your custom bundle instructions
```
