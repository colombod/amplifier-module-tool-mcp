# MCP Module Examples

This directory contains a working example showing how to use the MCP tool module with inline server configuration.

## Quick Start

```bash
amplifier bundle add git+https://github.com/microsoft/amplifier-module-tool-mcp@main#subdirectory=examples/bundle.md
amplifier bundle use mcp-example
```

Or copy it to customize:

```bash
curl -o my-mcp-bundle.md https://raw.githubusercontent.com/microsoft/amplifier-module-tool-mcp/main/examples/bundle.md
amplifier bundle use my-mcp-bundle.md
```

## What's Included

### bundle.md
Complete working example with inline MCP server configuration showing:
- **repomix** - Code packaging and analysis
- **context7** - Documentation search  
- **deepwiki** - GitHub repository documentation (Streamable HTTP transport example)

### mcp.json
Reference configuration file showing the same servers in JSON format (not used by the example bundle, provided for reference)

## Configuration Options

The example bundle uses inline configuration (servers defined directly in the bundle). You can also use external configuration files.

### Configuration Discovery Priority

The MCP module looks for server configuration in this order (highest priority first):

1. **Inline config** - `servers:` block in your bundle's tool config (used by example)
2. **Project config** - `.amplifier/mcp.json` in current directory
3. **User config** - `~/.amplifier/mcp.json` in home directory
4. **Environment variable** - `$AMPLIFIER_MCP_CONFIG` pointing to a JSON file

### Customizing the Example

Copy the bundle and modify the `servers:` section:

```yaml
tools:
  - module: tool-mcp
    source: git+https://github.com/microsoft/amplifier-module-tool-mcp@main
    config:
      servers:
        my-server:
          command: npx
          args: ["-y", "my-mcp-server"]
        # Add more servers here
```

### Using External Configuration Files

If you prefer to keep server configuration separate from your bundle:

```bash
# Copy the reference mcp.json to your project
cp examples/mcp.json .amplifier/mcp.json
# Edit .amplifier/mcp.json to customize

# Then use a minimal bundle without inline config
amplifier bundle use git+https://github.com/microsoft/amplifier-module-tool-mcp@main#subdirectory=behaviors/mcp.yaml
```

## Popular MCP Servers

See [MCP Server Registry](https://github.com/modelcontextprotocol/servers) for more servers.

**Note:** Amplifier's built-in filesystem and bash tools are recommended for file operations and shell commands rather than MCP filesystem servers.
