---
bundle:
  name: mcp-local-dev
  version: 1.0.0
  description: Local development bundle for testing MCP changes

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

tools:
  - module: tool-mcp
    source: file:///home/robotdad/Work/mcp/amplifier-module-tool-mcp
    config:
      servers:
        repomix:
          command: npx
          args: ["-y", "repomix", "--mcp"]
        context7:
          command: npx
          args: ["-y", "@upstash/context7-mcp"]
---

You are an AI assistant with MCP server capabilities enabled (LOCAL DEV VERSION).
