---
bundle:
  name: mcp-example
  version: 1.0.0
  description: Example bundle with MCP integration

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/robotdad/amplifier-module-tool-mcp@main#subdirectory=behaviors/mcp.yaml
---

You are an AI assistant with MCP server capabilities enabled.
