# MCP Module - Gap Analysis

**Date**: 2025-10-18
**Current Status**: Phase 3 complete, basic integration working
**Purpose**: Identify missing features from MCP specification

---

## 🎯 Current Implementation

### ✅ What We Have

| Feature | Status | Notes |
|---------|--------|-------|
| **stdio Transport** | ✅ Implemented | Working with repomix, context7 |
| **Tool Discovery** | ✅ Implemented | list_tools() |
| **Tool Execution** | ✅ Implemented | call_tool() |
| **Configuration** | ✅ Implemented | Multi-layer config loading |
| **Reconnection** | ✅ Implemented | Exponential backoff |
| **Circuit Breaker** | ✅ Implemented | 3-state FSM |
| **Health Monitoring** | ✅ Implemented | Status reporting |
| **Amplifier Integration** | ✅ Implemented | 19 tools registered |

---

## ❌ Critical Missing Features

### 1. Environment Variable Inheritance

**Problem**: Spawned MCP servers don't inherit parent session's environment

**Impact**:
- zen server fails (needs OPENAI_API_KEY)
- Other servers needing API keys won't work
- User has to duplicate env vars in config

**Example**:
```python
# Current (broken)
server_params = StdioServerParameters(
    command=self.command,
    args=self.args,
    env=self.env if self.env else None,  # Only uses config env
)

# Fixed (inherit + override)
server_params = StdioServerParameters(
    command=self.command,
    args=self.args,
    env={**os.environ, **self.env},  # Inherit parent, override with config
)
```

**Priority**: 🔴 **CRITICAL** - Blocks many servers

---

### 2. HTTP/SSE Transport

**Problem**: We only support stdio, but some servers use HTTP

**Impact**:
- deepwiki server doesn't work (uses HTTP)
- Any web-based MCP server won't work
- Limits integration to subprocess-based servers

**MCP Spec**: HTTP with Server-Sent Events transport
- Server exposes HTTP endpoint
- Client sends POST requests
- Server streams responses via SSE
- Supports multiple clients

**Implementation Needed**:
```python
from mcp.client.sse import sse_client

# HTTP/SSE connection
async with sse_client("http://localhost:3000/mcp") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
```

**Priority**: 🟡 **HIGH** - Needed for deepwiki and web servers

---

### 3. Streamable HTTP Transport (New Spec)

**Problem**: New MCP spec (2025-03-26) uses streamable HTTP, not SSE

**Impact**:
- Newer MCP servers use this transport
- We won't work with latest servers
- Missing modern features

**MCP Spec**: Streamable HTTP transport (replaces HTTP+SSE)
- Single HTTP endpoint (POST and GET)
- Optional SSE streaming
- Session management via headers
- Resumability with event IDs

**Implementation Needed**:
```python
from mcp.client.streamable_http import streamable_http_client

async with streamable_http_client("http://localhost:3000/mcp") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
```

**Priority**: 🟡 **MEDIUM** - For latest MCP servers

---

### 4. Resources Support

**Problem**: We only expose Tools, but MCP servers can also expose Resources

**MCP Spec**: Resources are files, data, or URIs that servers expose
- `list_resources()` - Discover available resources
- `read_resource(uri)` - Read resource content
- `subscribe()` - Get updates when resources change

**Examples**:
- File contents
- Database records
- API responses
- Live data feeds

**Impact**:
- Can't use resource-based servers
- Missing half of MCP's value proposition
- No file/data access from MCP servers

**Priority**: 🟡 **HIGH** - Core MCP feature

---

### 5. Prompts Support

**Problem**: We don't expose Prompts from MCP servers

**MCP Spec**: Prompts are reusable prompt templates
- `list_prompts()` - Discover available prompts
- `get_prompt(name, args)` - Get filled-in prompt
- Dynamic arguments

**Examples**:
- Code review templates
- Analysis prompts
- Task templates

**Impact**:
- Can't use prompt-based servers
- Missing LLM workflow integration

**Priority**: 🟢 **MEDIUM** - Nice to have

---

### 6. Sampling Support

**Problem**: We don't handle sampling requests from servers

**MCP Spec**: Servers can request LLM sampling
- `create_message` - Request LLM completion
- Server delegates reasoning to client's LLM
- Enables agentic behavior in servers

**Impact**:
- Can't use agentic MCP servers
- Servers can't leverage client's LLM
- Missing advanced use cases

**Priority**: 🟢 **LOW** - Advanced feature

---

### 7. Logging Support

**Problem**: We don't expose server logs to Amplifier

**MCP Spec**: Servers emit structured log messages
- `notifications/message` - Log notifications
- Different log levels
- Structured metadata

**Impact**:
- No visibility into server behavior
- Harder to debug issues
- Missing diagnostic information

**Priority**: 🟢 **MEDIUM** - Debugging aid

---

### 8. Progress Notifications

**Problem**: We don't handle progress updates from long-running operations

**MCP Spec**: Progress notifications for long operations
- `notifications/progress` - Progress updates
- Token for tracking
- Percentage complete

**Impact**:
- No feedback on long operations
- Poor UX for slow tools
- Can't show progress bars

**Priority**: 🟢 **LOW** - UX enhancement

---

## 📊 Feature Matrix

| Feature | MCP Spec | Our Status | Priority | Blocks |
|---------|----------|------------|----------|--------|
| stdio Transport | ✅ Required | ✅ Done | - | - |
| HTTP/SSE Transport | ✅ Standard | ❌ Missing | 🟡 HIGH | deepwiki |
| Streamable HTTP | ✅ New std | ❌ Missing | 🟡 MEDIUM | New servers |
| **Tools** | ✅ Core | ✅ Done | - | - |
| **Resources** | ✅ Core | ❌ Missing | 🟡 HIGH | Many servers |
| **Prompts** | ✅ Core | ❌ Missing | 🟢 MEDIUM | Workflow servers |
| Sampling | ⚪ Optional | ❌ Missing | 🟢 LOW | Agentic servers |
| Logging | ⚪ Optional | ❌ Missing | 🟢 MEDIUM | Debugging |
| Progress | ⚪ Optional | ❌ Missing | 🟢 LOW | Long operations |
| **Env Inheritance** | N/A | ❌ Missing | 🔴 CRITICAL | zen, others |

---

## 🔴 Critical Priority (Must Fix)

### 1. Environment Variable Inheritance

**Why Critical**:
- User has OPENAI_API_KEY set
- zen server doesn't get it
- Many servers need API keys
- Poor user experience

**Fix**:
```python
# In client.py, connect() method
import os

env = {**os.environ, **self.env}  # Inherit + override
server_params = StdioServerParameters(
    command=self.command,
    args=self.args,
    env=env,  # Pass merged environment
)
```

**Effort**: 5 minutes
**Impact**: Immediate - zen and other servers will work

---

## 🟡 High Priority (Should Add Soon)

### 2. HTTP/SSE Transport

**Why High**:
- deepwiki needs it
- Many web-based MCP servers use HTTP
- Standard transport type

**Implementation**:
```python
from mcp.client.sse import sse_client

class MCPHTTPClient:
    async def connect(self):
        read, write = await self._exit_stack.enter_async_context(
            sse_client(self.url)
        )
        # ... rest is similar
```

**Effort**: 2-3 hours
**Impact**: Unlocks web-based MCP servers

### 3. Resources Support

**Why High**:
- Core MCP feature (alongside Tools)
- Many servers expose resources
- File access, data feeds, etc.

**Implementation**:
```python
# In MCPClient
async def list_resources(self):
    result = await self.session.list_resources()
    return result.resources

async def read_resource(self, uri):
    result = await self.session.read_resource(uri)
    return result.contents

# In Amplifier integration
# Expose as tools or new primitive type
```

**Effort**: 4-6 hours
**Impact**: Access to server-provided files and data

---

## 🟢 Medium/Low Priority (Nice to Have)

### 4. Streamable HTTP Transport
- Newer spec (2025-03-26)
- Replaces SSE in some servers
- Better streaming support

**Effort**: 3-4 hours

### 5. Prompts Support
- Template system
- Workflow integration
- Reusable prompts

**Effort**: 3-4 hours

### 6. Sampling Support
- Agentic servers
- Server-initiated LLM calls
- Advanced use cases

**Effort**: 6-8 hours

### 7. Logging & Progress
- Better debugging
- UX improvements
- Visibility

**Effort**: 2-3 hours each

---

## 🎯 Recommended Roadmap

### Phase 4: Critical Fixes (Immediate)

**Duration**: 1-2 hours
**Blockers Removed**: zen server, many others

1. ✅ Fix environment variable inheritance
2. ✅ Test with zen server
3. ✅ Update documentation

**Outcome**: Most servers will work immediately

---

### Phase 5: HTTP Transport (Next Week)

**Duration**: 4-6 hours
**Servers Unlocked**: deepwiki, web-based servers

1. ✅ Implement HTTP/SSE client
2. ✅ Auto-detect transport type from config
3. ✅ Add HTTP-specific tests
4. ✅ Support both stdio and HTTP

**Outcome**: Universal MCP server support

---

### Phase 6: Resources (Following Week)

**Duration**: 6-8 hours
**Value Add**: File access, data resources

1. ✅ Implement resource discovery
2. ✅ Implement resource reading
3. ✅ Expose resources to Amplifier
4. ✅ Add resource subscriptions

**Outcome**: Full MCP feature parity

---

### Phase 7: Advanced Features (Future)

**Duration**: 10-15 hours total
**Features**: Streamable HTTP, Prompts, Sampling, Logging

Prioritize based on user needs and server adoption

---

## 📝 Missing Features Summary

### Transport Layer
- ❌ HTTP/SSE transport
- ❌ Streamable HTTP transport
- ❌ Custom transport plugin system

### MCP Primitives
- ✅ Tools (complete)
- ❌ Resources (missing)
- ❌ Prompts (missing)
- ❌ Sampling (missing)

### Operational Features
- ❌ Environment inheritance (CRITICAL)
- ❌ Logging notifications
- ❌ Progress notifications
- ❌ Server-initiated messages

### Quality of Life
- ❌ Auto-detect transport type
- ❌ Connection health checks
- ❌ Per-server configuration validation
- ❌ CLI management commands

---

## 🎓 Impact Analysis

### Without Fixes

**Working**: 3/5 servers (60%)
- ✅ repomix (stdio, no API key)
- ✅ context7 (stdio, no API key)
- ⚠️ browser-use (stdio but logs to stdout)
- ❌ zen (stdio but needs API key inheritance)
- ❌ deepwiki (HTTP transport)

**Tools Available**: 19 tools

### After Environment Fix

**Working**: 4/5 servers (80%)
- ✅ repomix
- ✅ context7
- ⚠️ browser-use
- ✅ zen (will work!)
- ❌ deepwiki (still needs HTTP)

**Tools Available**: ~25+ tools

### After HTTP Transport

**Working**: 5/5 servers (100%)
- All servers functional
- Full MCP ecosystem access

**Tools Available**: ~30+ tools

### After Resources Support

**Value**: Not just more tools, different capabilities
- File access from servers
- Database resources
- Live data feeds
- API proxy resources

---

## 🔧 Quick Wins

### 1. Environment Inheritance (5 min fix)

```python
# In client.py line 125
import os

env = {**os.environ, **self.env} if self.env else os.environ.copy()
server_params = StdioServerParameters(
    command=self.command,
    args=self.args,
    env=env,
)
```

**Impact**: zen server and others work immediately

### 2. Suppress browser-use stdout (Config change)

Remove browser-use from `.amplifier/mcp.json` or configure it differently.

**Impact**: Cleaner logs, no parse errors

### 3. Clean MCP Config for Working Servers

Only include servers that work:
```json
{
  "mcpServers": {
    "repomix": { "command": "npx", "args": ["-y", "repomix", "--mcp"] },
    "context7": { "command": "npx", "args": ["-y", "@upstash/context7-mcp"] },
    "zen": { "command": "uvx", "args": ["--from", "git+https://...", "zen-mcp-server"] }
  }
}
```

**Impact**: 3 fully working servers, no error spam

---

## 📋 Implementation Checklist

### Phase 4: Environment Fix (ASAP)
- [ ] Inherit os.environ in server spawn
- [ ] Test with zen server
- [ ] Verify API keys pass through
- [ ] Update tests
- [ ] Commit and document

### Phase 5: HTTP Transport (This Week)
- [ ] Implement HTTPMCPClient
- [ ] Add transport type detection
- [ ] Support SSE streaming
- [ ] Test with deepwiki
- [ ] Add HTTP integration tests

### Phase 6: Resources (Next Week)
- [ ] Implement list_resources()
- [ ] Implement read_resource()
- [ ] Wrap resources as Amplifier primitives
- [ ] Add resource tests
- [ ] Document resource usage

---

## 🎯 Success Criteria

### Phase 4 Success
- ✅ zen server connects and works
- ✅ No manual env var duplication needed
- ✅ All stdio servers working

### Phase 5 Success
- ✅ deepwiki connects successfully
- ✅ HTTP and stdio both supported
- ✅ 5/5 configured servers working

### Phase 6 Success
- ✅ Resources discoverable and readable
- ✅ File access from MCP servers
- ✅ Full MCP feature parity

---

## 🚀 Immediate Action Items

1. **Fix environment inheritance** (5 minutes)
2. **Test with zen server** (verify it works)
3. **Clean up mcp.json** (remove broken servers)
4. **Test actual tool execution** (end-to-end)
5. **Document working state** (what's usable now)

---

**Next Step**: Fix environment inheritance - it's a 5-minute change with massive impact!
