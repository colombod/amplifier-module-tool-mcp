---
bundle:
  name: mcp-example
  version: 1.0.0
  description: Example bundle with MCP integration

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

tools:
  - module: tool-mcp
    source: git+https://github.com/robotdad/amplifier-module-tool-mcp@main
    config:
      servers:
        repomix:
          command: npx
          args: ["-y", "repomix", "--mcp"]
        context7:
          command: npx
          args: ["-y", "@upstash/context7-mcp"]
        deepwiki:
          type: streamable-http
          url: https://mcp.deepwiki.com/mcp
---

You are an AI assistant with MCP server capabilities enabled.
