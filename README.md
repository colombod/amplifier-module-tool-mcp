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
  - module: provider-anthropic  # or provider-openai
    config:
      priority: 1
      default_model: claude-sonnet-4-5

tools:
  - module: tool-mcp
    source: git+https://github.com/robotdad/amplifier-module-tool-mcp@main
  - module: tool-filesystem
  - module: tool-bash
---

# My Profile with MCP

Your profile documentation goes here...
```

**Note:** The `source:` field enables auto-download from git. Users need collaborator access to your private repo and GitHub authentication configured.

Then use with Amplifier:

```bash
# Use the profile by name (from the name: field in the file)
amplifier run --profile my-profile "Use mcp_repomix_pack_codebase to analyze this project"
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
