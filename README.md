# Amplifier MCP Tool Module

**Status**: ✅ Production Ready  
**Version**: 0.2.0  
**Test Coverage**: 29/29 passing (100%)

MCP (Model Context Protocol) integration for Amplifier, enabling connection to MCP servers and exposing their capabilities (Tools, Resources, Prompts) to LLM agents.

---

## Features

- ✅ stdio and Streamable HTTP transport support (2025-03-26 MCP spec)
- ✅ Tools, Resources, and Prompts discovery
- ✅ Multi-server orchestration
- ✅ Environment variable inheritance
- ✅ Reconnection with exponential backoff
- ✅ Circuit breaker for failing servers
- ✅ Health monitoring
- ✅ Logging support

**Currently Working**: 60 capabilities from 5 MCP servers (41 tools + 19 prompts)

---

## Prerequisites

**Required**: Install [UV](https://docs.astral.sh/uv/) for package management:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Installation

### For Development

```bash
cd amplifier-module-tool-mcp
uv sync
```

### As a Bundle Behavior

The module is designed to be used as a bundle behavior. See the [Usage](#usage) section below.

---

## Configuration

### Server Configuration

Create `.amplifier/mcp.json`:

```json
{
  "mcpServers": {
    "repomix": {
      "command": "npx",
      "args": ["-y", "repomix", "--mcp"]
    },
    "zen": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/BeehiveInnovations/zen-mcp-server.git", "zen-mcp-server"]
    }
  }
}
```

### Module Configuration Options

The module can be configured via bundle behavior or direct module inclusion:

```yaml
# In your bundle.md or as a behavior
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

## Usage

### Using the Pre-configured Behavior

The easiest way to use this module is through the included behavior:

```bash
# Add the behavior to your bundle registry
amplifier bundle add git+https://github.com/robotdad/amplifier-module-tool-mcp@main#subdirectory=behaviors/mcp.yaml

# Use it in your bundle.md
---
bundle:
  name: my-bundle
  version: 1.0.0

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/robotdad/amplifier-module-tool-mcp@main#subdirectory=behaviors/mcp.yaml
---

# Your bundle instructions here
```

### Direct Module Integration

You can also add the module directly to your bundle:

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
      verbose_servers: false
      max_content_size: 50000
---

# Your bundle instructions here
```

### Running with MCP

```bash
# Set your bundle as current
amplifier bundle use my-bundle

# Run Amplifier (it will use MCP servers configured in .amplifier/mcp.json)
amplifier run "What MCP tools do you have?"
```

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
