# MCP Module Usage Examples

This directory contains examples showing how to use the MCP tool module with Amplifier.

---

## Quick Start

### 1. Copy Example Configuration

```bash
# Copy MCP server configuration
cp examples/mcp.json .amplifier/

# Or copy to user config for all projects
cp examples/mcp.json ~/.amplifier/mcp.json
```

### 2. Copy Example Profile

```bash
# Copy profile to your project
cp examples/profile-with-mcp.yaml .amplifier/profiles/my-mcp.yaml
```

### 3. Use with Amplifier

```bash
amplifier profile apply my-mcp
amplifier run
```

---

## Files

### `profile-with-mcp.yaml`

Complete Amplifier profile with MCP tools enabled.

**Shows:**
- How to add tool-mcp to a profile
- Optional inline server configuration
- Integration with standard tools

**Usage:**
```bash
amplifier run --profile examples/profile-with-mcp.yaml "What tools are available?"
```

### `mcp.json`

Example MCP server configurations.

**Includes:**
- **repomix** - Code analysis (7 tools)
- **context7** - Documentation search (2 tools)
- **zen** - AI workflows (18 tools + 19 prompts)
- **browser-use** - Browser automation (11 tools)
- **deepwiki** - HTTP example (GitHub docs)
- **filesystem** - Official MCP server example

**Notes included for:**
- Which servers need API keys
- Transport types (stdio vs HTTP)
- Configuration requirements

---

## Example Usage Scenarios

### Scenario 1: Code Analysis

**Goal**: Analyze a codebase for insights

**MCP Servers Needed**: repomix

**Configuration**:
```json
{
  "mcpServers": {
    "repomix": {
      "command": "npx",
      "args": ["-y", "repomix", "--mcp"]
    }
  }
}
```

**Usage**:
```bash
amplifier run "Use mcp_repomix_pack_codebase to analyze the current directory"
```

**What You Get**:
- Code packaging for LLM analysis
- Pattern searching in packaged code
- Directory structure analysis

---

### Scenario 2: Documentation Search

**Goal**: Find library documentation quickly

**MCP Servers Needed**: context7

**Configuration**:
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

**Usage**:
```bash
amplifier run "Use mcp_context7_get-library-docs to find React hooks documentation"
```

**What You Get**:
- Up-to-date library documentation
- API references
- Code examples

---

### Scenario 3: AI-Powered Development Workflows

**Goal**: Use structured AI workflows for code review, debugging, etc.

**MCP Servers Needed**: zen

**Prerequisites**: `OPENAI_API_KEY` environment variable

**Configuration**:
```json
{
  "mcpServers": {
    "zen": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/BeehiveInnovations/zen-mcp-server.git",
        "zen-mcp-server"
      ]
    }
  }
}
```

**Usage - Tools**:
```bash
amplifier run "Use mcp_zen_codereview to review src/main.py"
amplifier run "Use mcp_zen_debug to help debug this error"
amplifier run "Use mcp_zen_secaudit for security analysis"
```

**Usage - Prompts** (Multi-step workflows):
```bash
amplifier run "Use mcp_zen_prompt_thinkdeeper to analyze this architecture"
amplifier run "Use mcp_zen_prompt_consensus on this technical decision"
amplifier run "Use mcp_zen_prompt_review for code review workflow"
```

**What You Get**:
- 18 development tools (code review, debugging, security, etc.)
- 19 workflow prompts (deep thinking, consensus, planning, etc.)
- Structured multi-step AI processes

---

### Scenario 4: Browser Automation

**Goal**: Automate web interactions

**MCP Servers Needed**: browser-use

**Prerequisites**: `OPENAI_API_KEY` environment variable

**Configuration**:
```json
{
  "mcpServers": {
    "browser-use": {
      "command": "uvx",
      "args": ["browser-use[cli]==0.5.10", "--mcp"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

**Usage**:
```bash
amplifier run "Use mcp_browser-use_browser_navigate to open github.com"
amplifier run "Use browser tools to extract data from this website"
```

**What You Get**:
- Browser navigation and interaction
- Web scraping
- Form filling
- Content extraction

---

### Scenario 5: Complete Setup (All Servers)

**Goal**: Maximum capability

**Configuration**: Use the provided `examples/mcp.json` as-is

**Prerequisites**:
```bash
export OPENAI_API_KEY=sk-...
# or
export ANTHROPIC_API_KEY=sk-ant-...
```

**Usage**:
```bash
# Copy full configuration
cp examples/mcp.json .amplifier/

# Use the example profile
amplifier run --profile examples/profile-with-mcp.yaml

# Now you have 57+ capabilities!
```

**What You Get**:
- 38 tools across 4 servers
- 19 AI workflow prompts
- Code analysis, docs, browser automation, AI workflows

---

## Troubleshooting

### Server Won't Start

**Check environment variables**:
```bash
# Some servers need API keys
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Set if missing
export OPENAI_API_KEY=sk-...
```

**Check server is installed**:
```bash
# For npx servers
npx -y repomix --mcp  # Should show "running on stdio"

# For uvx servers
uvx --from git+https://... zen-mcp-server  # Should start
```

### Tools Not Showing Up

**Verify profile**:
```bash
amplifier profile show my-mcp
# Should show "tool-mcp" in Tools section
```

**Check logs**:
```bash
amplifier logs
# Look for "Mounted MCP tool" messages
```

### Connection Errors

Some servers may:
- Be rate-limited (deepwiki)
- Require specific versions
- Have compatibility issues

**Solution**: Start with simple servers (repomix, context7) first.

---

## Creating Custom MCP Server Configurations

### Minimal stdio Server

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "my-mcp-package"]
    }
  }
}
```

### HTTP Server

```json
{
  "mcpServers": {
    "my-http-server": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

### Server with Environment Variables

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "env": {
        "API_KEY": "${MY_API_KEY}",
        "DEBUG": "true"
      }
    }
  }
}
```

### Streamable HTTP (Latest Spec)

```json
{
  "mcpServers": {
    "new-server": {
      "type": "streamable-http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

---

## MCP Server Discovery

### Official MCP Servers

Find more at:
- https://github.com/modelcontextprotocol/servers
- https://mcp.directory (community directory)

### Popular Third-Party Servers

- **repomix** - Code packaging
- **zen** - AI development workflows
- **context7** - Documentation search
- **browser-use** - Browser automation
- **deepwiki** - GitHub repo docs

---

## Best Practices

### Start Simple

1. Start with 1-2 servers (repomix, context7)
2. Test that they work
3. Add more as needed

### Environment Management

```bash
# Set in your shell profile (.zshrc, .bashrc)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Or use .env file (if your profile supports it)
```

### Progressive Enhancement

**Minimal**:
```json
{"mcpServers": {"repomix": {...}}}
```

**Add capabilities**:
```json
{"mcpServers": {
  "repomix": {...},
  "context7": {...}
}}
```

**Full power**:
```json
{"mcpServers": {
  "repomix": {...},
  "context7": {...},
  "zen": {...},
  "browser-use": {...}
}}
```

---

## Next Steps

1. Copy `examples/mcp.json` to `.amplifier/mcp.json`
2. Copy `examples/profile-with-mcp.yaml` to `.amplifier/profiles/`
3. Run: `amplifier profile apply <profile-name>`
4. Try: `amplifier run "What MCP tools do you have?"`

**See the main README.md for more details!**
