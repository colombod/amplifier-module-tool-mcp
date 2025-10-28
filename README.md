# Amplifier MCP Tool Module

**Status**: ✅ Production Alpha - Fully Functional  
**Version**: 0.1.0  
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

## Installation

```bash
cd amplifier-module-tool-mcp
uv pip install -e .
```

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

Configure in your profile:

```yaml
tools:
  - module: tool-mcp
    source: git+https://github.com/robotdad/amplifier-module-tool-mcp@main
    config:
      # Server output control
      verbose_servers: false  # Default: suppress MCP server debug output
      server_log_dir: ~/.amplifier/logs/mcp-servers/  # Where logs are saved when suppressed

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
| `servers` | (optional) | Inline server configuration (overrides .amplifier/mcp.json) |

**Environment variable override**:
```bash
# Enable verbose output without changing profile
AMPLIFIER_MCP_VERBOSE=true amplifier run --profile mcp-example "test"
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

Add to your Amplifier profile (`.amplifier/profiles/my-profile.md`):

```yaml
---
profile:
  name: my-profile
  extends: base

session:
  orchestrator:
    module: loop-basic
  context:
    module: context-simple

providers:
  - module: provider-anthropic
    source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main
    config:
      priority: 1
      default_model: claude-sonnet-4-5

tools:
  - module: tool-mcp
    source: git+https://github.com/robotdad/amplifier-module-tool-mcp@main
    config:
      verbose_servers: false  # Optional: set to true to see server debug output
  - module: tool-filesystem
    source: git+https://github.com/microsoft/amplifier-module-tool-filesystem@main
  - module: tool-bash
    source: git+https://github.com/microsoft/amplifier-module-tool-bash@main
---

# My Profile with MCP

Your profile documentation goes here...
```

Then use with Amplifier:

```bash
# Use the profile by name (from the name: field in the file)
amplifier run --profile my-profile "What MCP tools do you have?"
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
