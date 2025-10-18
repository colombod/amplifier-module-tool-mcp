# Amplifier MCP Tool Module

**Status**: Alpha Development
**Version**: 0.1.0

MCP (Model Context Protocol) integration for Amplifier, enabling connection to MCP servers and exposing their tools to LLM agents.

## Features

- Connect to MCP servers (stdio transport)
- Automatic tool discovery
- Tool lifecycle management
- Event-driven observability
- Configuration via `.amplifier/mcp.json` (Claude Code compatible)

## Installation

```bash
# From source
cd amplifier-module-tool-mcp
uv pip install -e .
```

## Configuration

Create `.amplifier/mcp.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
    }
  }
}
```

## Usage

Add to your Amplifier profile:

```yaml
tools:
  - module: tool-mcp
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check .
```

## Documentation

See `/ai_working/mcp/` in amplifier-dev for complete implementation plan and architecture docs.

## License

MIT
