# Amplifier MCP Tool Module

Modular capability that adds Model Context Protocol (MCP) server integration to Amplifier bundles.

## Overview

This module enables Amplifier to connect to MCP servers and expose their capabilities (Tools, Resources, Prompts) to LLM agents. Connect to any MCP-compatible server and make its tools available to your AI agents.

**What You Get:**
- 🔌 **Multi-server orchestration** - Connect to multiple MCP servers simultaneously
- 🚀 **Dual transport support** - stdio and Streamable HTTP (2025-03-26 MCP spec)
- 🔄 **Auto-reconnection** - Exponential backoff with circuit breaker for resilience
- 🛡️ **Content protection** - Automatic truncation to prevent context exhaustion
- 📊 **Health monitoring** - Track server status and connection health
- 🔇 **Clean console** - Server logs saved to files, not cluttering output

**Production Proven:** 60 capabilities from 5 MCP servers (41 tools + 19 prompts)

**Status:** ✅ Production Ready | **Version:** 0.2.0 | **Tests:** 46/46 passing

---

## Prerequisites

- **Python 3.11+**
- **[UV](https://github.com/astral-sh/uv)** - Fast Python package manager

### Installing UV

```bash
# macOS/Linux/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Installation

### Recommended: Include the Behavior

Add MCP capability to your bundle by including the behavior:

```yaml
---
bundle:
  name: my-bundle
  version: 1.0.0
  description: My custom bundle with MCP support

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/robotdad/amplifier-module-tool-mcp@main#subdirectory=behaviors/mcp.yaml
---

# Your bundle instructions...
```

**What this gives you:**
- ✅ MCP tool module configured with production defaults
- ✅ Content size protection enabled (50k char limit)
- ✅ Clean console output (server logs saved to files)
- ✅ Automatic server discovery from `.amplifier/mcp.json`
- ✅ Clean dependency chain (no redundant includes)

**Why this pattern?**
- You control your foundation version
- Explicit about what capabilities you're adding
- Production-ready defaults out of the box
- Easy to customize configuration if needed

### Alternative: Direct Module Integration

You can also add the module directly with custom configuration:

```yaml
---
bundle:
  name: my-bundle
  version: 1.0.0

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

tools:
  - module: tool-mcp
    source: git+https://github.com/robotdad/amplifier-module-tool-mcp@main
    config:
      verbose_servers: true  # Custom: show server output
      max_content_size: 100000  # Custom: larger content limit
---

# Your bundle instructions...
```

### For Module Development

If you're developing the tool-mcp module itself:

```bash
cd amplifier-module-tool-mcp
uv sync
```

---

## Quick Start

### 1. Add MCP to Your Bundle

```yaml
# your-bundle.md
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/robotdad/amplifier-module-tool-mcp@main#subdirectory=behaviors/mcp.yaml
```

### 2. Configure MCP Servers

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

**Popular MCP Servers:**
- `@modelcontextprotocol/server-postgres` - PostgreSQL database operations
- `@modelcontextprotocol/server-puppeteer` - Web automation and scraping
- `@modelcontextprotocol/server-sqlite` - SQLite database operations
- `@modelcontextprotocol/server-brave-search` - Web search via Brave API
- See [MCP Server Registry](https://github.com/modelcontextprotocol/servers) for more

**Note:** Amplifier's built-in filesystem and bash tools are recommended for file operations and shell commands rather than MCP filesystem servers.

### 3. Use Your Bundle

```bash
amplifier bundle use your-bundle.md
amplifier run "What MCP tools are available?"
```

The agent will automatically discover and use tools from your configured MCP servers!

### Complete Example

See `examples/mcp-example.md` for a complete working bundle showing:
- How to include the MCP behavior in your bundle
- Server configuration examples
- Usage instructions
- Customization options

---

## Configuration

### Module Configuration Options

The module can be configured via bundle behavior or direct module inclusion:

```yaml
# In your bundle.md
tools:
  - module: tool-mcp
    source: git+https://github.com/robotdad/amplifier-module-tool-mcp@main
    config:
      # Server output control
      verbose_servers: false  # Default: suppress MCP server debug output
      server_log_dir: ~/.amplifier/logs/mcp-servers/  # Where logs are saved when suppressed
      
      # Content size protection (prevents context exhaustion)
      max_content_size: 50000  # Default: 50k chars (~12k tokens)

      # Optional inline server config (overrides .amplifier/mcp.json)
      servers:
        my-server:
          command: npx
          args: ["-y", "my-mcp-server"]
```

**Configuration options**:

| Option | Default | Description |
|--------|---------|-------------|
| `verbose_servers` | `false` | Show MCP server stderr output in console |
| `server_log_dir` | `~/.amplifier/logs/mcp-servers/` | Directory for server logs when suppressed |
| `max_content_size` | `50000` | Maximum content size in characters. Content exceeding this limit is automatically truncated with a notice to prevent context window exhaustion |
| `servers` | (optional) | Inline server configuration (overrides .amplifier/mcp.json) |

**Environment variable override**:
```bash
# Enable verbose output without changing bundle config
AMPLIFIER_MCP_VERBOSE=true amplifier run "test"
```

**When to use verbose mode**:
- Debugging MCP server connection issues
- Diagnosing tool execution failures
- Understanding server initialization

**Default behavior (quiet)**:
- Clean console output
- Server logs saved to `~/.amplifier/logs/mcp-servers/{server-name}.log`
- Check logs if server connection fails

---

### Configuration Priority

1. **Inline config** (servers in bundle config) - highest priority
2. **Project config** (`.amplifier/mcp.json`) - recommended
3. **User config** (`~/.amplifier/mcp.json`) - fallback
4. **Environment variable** (`AMPLIFIER_MCP_CONFIG`) - override

## Usage

### How MCP Tools Appear to Agents

Once configured, MCP server tools become available like any other Amplifier tool:

```
User: "List files in the project"

Agent: [Uses mcp_filesystem_list_directory tool from MCP server]
Response: [Directory listing from MCP filesystem server]
```

All MCP tools are prefixed with `mcp_{server}_{tool}` to avoid naming conflicts.

### Example: Using Multiple MCP Servers

```yaml
---
bundle:
  name: data-assistant
  version: 1.0.0

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/robotdad/amplifier-module-tool-mcp@main#subdirectory=behaviors/mcp.yaml
---

You are a data assistant with access to databases and web automation via MCP.

Use postgres tools for database operations.
Use puppeteer tools for web scraping and automation.
```

With `.amplifier/mcp.json`:
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

Agent gets tools like:
- `mcp_postgres_query` - Execute SQL queries
- `mcp_postgres_list_tables` - List database tables
- `mcp_puppeteer_navigate` - Navigate to URLs
- `mcp_puppeteer_screenshot` - Capture screenshots

---

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/test_integration.py -v
```

---

## Documentation

See complete documentation in:
- `EXECUTIVE_SUMMARY.md` - Overview and status
- `SDK_CAPABILITIES.md` - What the SDK provides
- `GAP_ANALYSIS.md` - Feature analysis
- `PHASE4_SUMMARY.md` - Latest features

---

## License

MIT
