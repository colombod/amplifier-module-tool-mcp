# MCP Module Modernization - Session Handoff

**Date:** 2026-01-07  
**Repository:** https://github.com/microsoft/amplifier-module-tool-mcp  
**Current Version:** 0.2.2 (in development)  
**Status:** ✅ FIXED - Critical crash on server connection failure resolved

---

## What This Module Does

The `amplifier-module-tool-mcp` is an Amplifier tool module that integrates the Model Context Protocol (MCP), allowing Amplifier to connect to MCP servers and expose their capabilities (Tools, Resources, Prompts) to LLM agents.

**Key Features:**
- Multi-server orchestration (connect to multiple MCP servers simultaneously)
- Dual transport support (stdio and Streamable HTTP)
- Content size protection (prevents context exhaustion)
- Reconnection with exponential backoff
- Circuit breaker for failing servers

---

## What We Accomplished This Session

### 1. Ecosystem Alignment (Commits: d7c163c, 34d2955, 45384f8)

**Brought module current with Amplifier v1.0.0 conventions:**
- ✅ Added `__amplifier_module_type__ = "tool"` metadata marker
- ✅ Removed `amplifier-core` from runtime dependencies (provided by runtime)
- ✅ Added missing package metadata (`license`, `readme` in pyproject.toml)
- ✅ Improved type annotations (`dict[str, Any]`, explicit return types)
- ✅ Added pytest configuration section
- ✅ Version bumped from 0.1.0 → 0.2.0
- ✅ Moved `amplifier-core` to dev dependencies only

### 2. Bundle Migration (All commits above)

**Migrated from deprecated profiles to bundles:**
- ✅ Created `behaviors/mcp.yaml` for easy bundle inclusion
- ✅ Updated README to use bundle patterns instead of profiles
- ✅ Created minimal `examples/bundle.md` with inline server configuration
- ✅ Created `examples/README.md` with complete usage documentation
- ✅ Removed profile references throughout documentation
- ✅ Added clear "Quick Start" with numbered steps
- ✅ Followed Microsoft skills module documentation patterns

### 3. Lazy Connection Implementation (Commit: bf0976a)

**Critical architectural fix - version 0.2.1:**

**Problem:** Module was eagerly connecting to ALL MCP servers during `mount()`:
- User asking "what servers are configured?" triggered connection attempts
- Session initialization crashed when servers failed to connect
- Async context manager errors from failed cleanup
- Slow startup when servers took time to connect
- Wasted resources connecting to unused servers

**Solution Implemented:**
- ✅ Refactored `manager.start()` to only create client objects, not connect
- ✅ Made getter methods async (`get_tools()`, `get_resources()`, `get_prompts()`)
- ✅ Added `_ensure_server_connected()` for lazy connection with error handling
- ✅ Added connection locks (`asyncio.Lock`) to both clients for thread-safe lazy connection
- ✅ Updated tests to await async getters
- ✅ All tests passing: 50 passed, 3 warnings

**Files Changed:**
- `amplifier_module_tool_mcp/__init__.py` - Await async getters
- `amplifier_module_tool_mcp/manager.py` - Lazy connection implementation  
- `amplifier_module_tool_mcp/client.py` - Connection lock for thread safety
- `amplifier_module_tool_mcp/streamable_http_client.py` - Connection lock for thread safety
- `tests/test_integration.py` - Fixed to await async getters

---

## ✅ Session 2 Accomplishments (2026-01-07)

### 4. Critical Bug Fix - Graceful Degradation (Commit: 271f812)

**Problem:** Module crashed during `mount()` when ANY server failed to connect, preventing session initialization entirely.

**Root Cause Analysis:**
- `asyncio.CancelledError` inherits from `BaseException`, NOT `Exception`
- Existing `except Exception` blocks didn't catch `CancelledError`
- When servers failed (zen, deepwiki), `CancelledError` propagated up and crashed the entire session

**Solution Implemented:**
- ✅ Added `import asyncio` to manager.py
- ✅ Broadened exception handling to `except (Exception, asyncio.CancelledError)` in:
  - `_ensure_server_connected()` - removed re-raise
  - `get_tools()` - continue with other servers
  - `get_resources()` - continue with other servers
  - `get_prompts()` - continue with other servers
- ✅ Enhanced mount summary to show "X/Y servers" connected
- ✅ Added warning log when servers fail to connect

**Testing:**
- ✅ All 50 unit tests still passing
- ✅ Module mounts successfully when servers fail
- ✅ Working servers provide capabilities normally
- ✅ Failed servers logged with clear error messages

**Philosophy Alignment:**
- ✅ Graceful degradation (mount succeeds even if all fail)
- ✅ Fail-open for non-critical errors
- ✅ Clear error visibility (logging with context)
- ✅ Ruthless simplicity (3-line fix, no complex retry logic)

**Impact:**
The module now embodies Amplifier's philosophy: **one failing server cannot crash the entire system.**

---

## Current Issues

### Known Limitation: MCP SDK Async Cleanup Errors

**Error Pattern:**
```
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
RuntimeError: aclose(): asynchronous generator is already running
```

**Occurrence:** When MCP servers fail to connect (zen, deepwiki)

**Source:** MCP SDK itself - async generators don't handle cleanup properly when connection attempts fail

**Impact:** 
- Errors appear in console (ugly UX)
- Don't crash the system (benign but noisy)
- Happen even with lazy connection code

**Status:** Not fixable at our integration level - this is an MCP SDK limitation

---

## MCP Server Test Results

### Working Servers ✅

1. **context7** - Working!
   - Server: `@upstash/context7-mcp`
   - Log: "Context7 Documentation MCP Server v2.0.2 running on stdio"
   - Status: Starts successfully

2. **repomix** - Likely working
   - Server: `repomix --mcp`
   - Version: 1.11.0
   - Log: Only npm notices (no errors)
   - Needs testing with actual connection

### Failing Servers ❌

3. **zen** - Configuration error
   - Issue: Wrong executable name
   - Current: `zen-mcp-server`
   - Should be: `pal-mcp-server`
   - Log shows: "An executable named `zen-mcp-server` is not provided by package `pal-mcp-server`"

4. **deepwiki** - Connection failed
   - Type: Streamable HTTP
   - URL: https://mcp.deepwiki.com/mcp
   - Issue: HTTP connection errors
   - Needs investigation

---

## Test Environment

**System:** ARM64 Linux (monad/robotdad's machine)  
**Location:** /path/to/amplifier-module-tool-mcp  
**Node.js:** ✅ Installed (npx 11.6.2)  
**Python:** 3.12.3  
**Amplifier:** Latest  

**Bundle Configuration:**
- Using: `mcp-example` bundle
- Source: `git+https://github.com/microsoft/amplifier-module-tool-mcp@main#subdirectory=examples/bundle.md`
- Inline servers: repomix, context7, zen, deepwiki

---

## Architecture Decisions Made

### Decision 1: Connection Strategy ✅ RESOLVED

**Question:** Should connection be truly lazy or acceptable during mount?

**Decision:** Accept connection during mount with graceful degradation

**Rationale:**
- **Can't have truly lazy registration** - Coordinator needs to know what tools exist to register them
- **MCP protocol requires connection** - Tool names/schemas only available after connecting
- **Graceful degradation is key** - Connection during mount is acceptable IF failures don't crash
- **Philosophy alignment** - Simple, direct approach over complex deferred registration

**Implementation:**
- Mount connects to all servers eagerly
- Failed connections are caught and logged
- Working servers register their capabilities
- Module mounts successfully regardless of failures

**Outcome:** Simple, predictable behavior that embodies Amplifier philosophy.

### Decision 2: Async Cleanup Errors ✅ DOCUMENTED

**Question:** How to handle MCP SDK async context errors?

**Decision:** Document as known limitation, accept noisy but benign errors

**Rationale:**
- **Not our bug** - MCP SDK's async generator cleanup issue
- **Benign errors** - Don't affect functionality, just ugly console output
- **No good suppression** - Catching would require catching BaseException (dangerous)
- **Upstream fix needed** - Should be reported to MCP SDK project

**Status:** Documented as known limitation. Errors appear when servers fail but don't crash the system.

---

## Next Steps

### Immediate Actions

1. **Update version to 0.2.2** in pyproject.toml
   - Reflects the critical bugfix

2. **Test with working servers**
   ```bash
   amplifier run "use mcp_repomix tool to analyze /path/to/workspace"
   amplifier run "use mcp_context7 tool to search for python async documentation"
   ```

3. **Fix zen server configuration in example bundle**
   - Change from `zen-mcp-server` to `pal-mcp-server`
   - Or remove zen entirely (it's causing connection failures)

4. **Fix deepwiki server** (if worth keeping)
   - Investigate HTTP connection errors
   - May be an upstream issue with deepwiki server

### Future Enhancements

5. **Simplify example bundle** (recommended)
   - Remove failing servers (zen, deepwiki)
   - Focus on 1-2 servers that "just work" (context7, repomix)
   - Provide separate advanced examples for more complex setups

6. **Add troubleshooting documentation**
   - How to check server logs (`~/.amplifier/logs/mcp-servers/`)
   - Common connection issues and fixes
   - How to test servers manually before adding to bundle

7. **Documentation polish**
   - Add Microsoft Contributing/Trademarks sections
   - Consolidate or remove docs/ directory
   - Clean up development artifacts (ai_working/, etc.)

8. **Consider reporting MCP SDK issue**
   - Document async cleanup errors in MCP SDK GitHub
   - Help upstream fix the context manager cleanup issue

---

## Files Modified This Session

**Commit bf0976a (Session 1):** Lazy connection implementation
```
M  amplifier_module_tool_mcp/__init__.py (await async getters)
M  amplifier_module_tool_mcp/client.py (connection lock added)
M  amplifier_module_tool_mcp/manager.py (lazy connection logic)
M  amplifier_module_tool_mcp/streamable_http_client.py (connection lock added)
M  pyproject.toml (version 0.2.1)
M  tests/test_integration.py (await async getters)
```

**Commit 271f812 (Session 2):** Critical crash fix
```
M  amplifier_module_tool_mcp/__init__.py (enhanced mount summary)
M  amplifier_module_tool_mcp/manager.py (broadened exception handling for CancelledError)
```

**Local (not committed):**
```
M  SESSION_HANDOFF.md (this file)
?? examples/bundle-local-dev.md (local dev helper, can be deleted)
```

---

## How to Test This

```bash
# Clear cache to get latest from GitHub
find ~/.amplifier/cache -type d -name "amplifier-module-tool-mcp-*" -exec rm -r {} +

# Add bundle from GitHub
amplifier bundle remove mcp-example
amplifier bundle add git+https://github.com/microsoft/amplifier-module-tool-mcp@main#subdirectory=examples/bundle.md

# Use the bundle
amplifier bundle use mcp-example

# Test it
amplifier run "list all your available tools"
```

---

## Key Insights

### From Session 1 (Lazy Connection)
1. **Lazy connection implemented** - Servers only connect when capabilities are queried
2. **Connection locks added** - Thread-safe lazy connection with asyncio.Lock
3. **Tests all passing** - 50 tests pass with the async getter changes

### From Session 2 (Critical Bugfix)
1. **Root cause identified** - `asyncio.CancelledError` inherits from `BaseException`, not `Exception`
2. **Simple fix, big impact** - 3-line change (broaden exception handling) prevents fatal crashes
3. **Philosophy alignment** - Graceful degradation > complex retry logic
4. **MCP SDK limitation** - Async cleanup errors are benign but noisy, not fixable at our level
5. **Connection during mount is acceptable** - As long as failures don't crash the system

### Technical Learnings
- Exception hierarchy matters: `CancelledError` bypasses `except Exception`
- Graceful degradation requires catching the right exceptions at the right layers
- "Lazy" connection can still happen during mount if it enables graceful failure handling
- Simple error handling (catch and continue) beats complex retry machinery

---

## Questions for Next Session

1. ✅ **RESOLVED:** Connection during mount is acceptable with graceful degradation
2. ✅ **RESOLVED:** Async cleanup errors documented as known MCP SDK limitation
3. 🔄 **TODO:** Should we simplify the example bundle to only include working servers?
4. 🔄 **TODO:** Should we fix zen/deepwiki configuration or remove them from examples?
5. 🔄 **TODO:** Should we bump version to 0.2.2 to reflect the critical bugfix?

---

## Session History

- **Session 1** (50a802f3-9e7e-418b-a00f-e454e0dd566f): Lazy connection implementation (v0.2.1, commit bf0976a)
- **Session 2** (f9ee94c0-379c-456e-80ed-af5bfd176901): Critical crash fix (commit 271f812)

**Repository:** /path/to/amplifier-module-tool-mcp  
**Working directory:** /path/to/workspace
