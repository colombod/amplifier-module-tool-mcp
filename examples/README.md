# MCP Module Examples

This directory contains a working example showing how to use the MCP tool module.

## Quick Start

### 1. Copy the MCP server configuration to your project

```bash
cp examples/mcp.json .amplifier/mcp.json
```

Or set an environment variable to use it directly:

```bash
export AMPLIFIER_MCP_CONFIG=/path/to/amplifier-module-tool-mcp/examples/mcp.json
```

### 2. Use the example bundle

```bash
# Use directly from the examples directory
amplifier bundle use examples/bundle.md
amplifier run "What MCP tools are available?"

# Or copy to your project
cp examples/bundle.md my-mcp-bundle.md
amplifier bundle use my-mcp-bundle.md
```

## What's Included

### bundle.md
Minimal bundle that adds MCP capability to foundation. No documentation in the bundle itself - just includes foundation and the MCP behavior.

### mcp.json
Example MCP server configurations showing:
- **repomix** - Code packaging and analysis
- **context7** - Documentation search
- **zen** - AI-powered development workflows (requires OPENAI_API_KEY)
- **deepwiki** - GitHub repository documentation (Streamable HTTP example)

## Configuration Discovery

The MCP module looks for server configuration in this order (highest priority first):

1. **Inline config** - `servers:` block in your bundle's tool config
2. **Project config** - `.amplifier/mcp.json` in current directory
3. **User config** - `~/.amplifier/mcp.json` in home directory
4. **Environment variable** - `$AMPLIFIER_MCP_CONFIG` pointing to a JSON file

## Customizing Configuration

### Option 1: Copy and Modify mcp.json

```bash
cp examples/mcp.json .amplifier/mcp.json
# Edit .amplifier/mcp.json to add/remove servers
```

### Option 2: Inline Configuration

Create your own bundle with inline server config:

```yaml
---
bundle:
  name: my-mcp-bundle
  version: 1.0.0

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

tools:
  - module: tool-mcp
    source: git+https://github.com/robotdad/amplifier-module-tool-mcp@main
    config:
      servers:
        my-server:
          command: npx
          args: ["-y", "my-mcp-server"]
---

Your bundle instructions here.
```

### Option 3: Environment Variable

```bash
# Point to any mcp.json file
export AMPLIFIER_MCP_CONFIG=/path/to/my-mcp-servers.json
amplifier run "test"
```

## Popular MCP Servers

See [MCP Server Registry](https://github.com/modelcontextprotocol/servers) for more servers.

**Note:** Amplifier's built-in filesystem and bash tools are recommended for file operations and shell commands rather than MCP filesystem servers.
