# Amplifier MCP Tool Module

**Status**: ✅ Production Alpha - Fully Functional  
**Version**: 0.1.0  
**Test Coverage**: 29/29 passing (100%)

MCP (Model Context Protocol) integration for Amplifier, enabling connection to MCP servers and exposing their capabilities (Tools, Resources, Prompts) to LLM agents.

---

## Features

- ✅ stdio and HTTP/SSE transport support
- ✅ Tools, Resources, and Prompts discovery
- ✅ Multi-server orchestration
- ✅ Environment variable inheritance
- ✅ Reconnection with exponential backoff
- ✅ Circuit breaker for failing servers
- ✅ Health monitoring
- ✅ Logging support

**Currently Working**: 57+ capabilities from 4 MCP servers (38 tools + 19 prompts)

---

## Installation

```bash
cd amplifier-module-tool-mcp
uv pip install -e .
```

---

## Configuration

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

---

## Usage

Add to your Amplifier profile:

```yaml
---
profile:
  name: my-profile
  extends: full-openai

tools:
  - module: tool-mcp
---
```

Then use with Amplifier:

```bash
amplifier profile apply my-profile
amplifier run "Use mcp_repomix_pack_codebase to analyze this project"
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
