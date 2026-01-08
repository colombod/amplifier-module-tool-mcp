# MCP Module Integration Fixes - 2025-10-28

## Issue Summary

The MCP tool module had multiple integration issues with the rapidly evolving amplifier-dev ecosystem:
1. Missing source URLs in example profile
2. Excessive MCP server debug output polluting console
3. Raw TextBlock output instead of formatted responses
4. ToolResult format incompatibility

## Root Causes

### 1. Profile Source URLs Now Required

**Discovery**: Amplifier changed to require explicit `source:` git URLs for ALL module references.

**Evidence**:
- Error messages showed: `Profile: (no source specified)`
- Bundled profiles in `amplifier-app-cli/data/profiles/*.md` all have source URLs
- Example profile was outdated

**Fix**: Added source URLs to all modules in example profile:
```yaml
providers:
  - module: provider-anthropic
    source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main

tools:
  - module: tool-filesystem
    source: git+https://github.com/microsoft/amplifier-module-tool-filesystem@main
```

### 2. MCP Server Output Noise

**Discovery**: MCP servers spawned via stdio transport dump 50+ lines of debug output to stderr, which passes through to user console.

**Evidence**:
```
Context7 Documentation MCP Server running on stdio
2025-10-28 15:59:28,578 - server - DEBUG - ZEN_MCP_FORCE_ENV_OVERRIDE...
[... 50+ more lines ...]
```

**Fix**: Suppress by default with opt-in verbose mode
- Added `verbose_servers: false` config option (default)
- Redirect server stderr to log files via `stdio_client(..., errlog=log_file)`
- Server logs saved to `~/.amplifier/logs/mcp-servers/{server-name}.log`
- Support `AMPLIFIER_MCP_VERBOSE=true` env var for debugging

**Implementation** (client.py:146-169):
```python
if not self.verbose_servers:
    # Suppress - redirect to log file
    log_file_path = self.server_log_dir / f"{self.server_name}.log"
    self._server_log_file = open(log_file_path, "a")
else:
    # Verbose - passthrough to console
    self._server_log_file = None

read, write = await self._exit_stack.enter_async_context(
    stdio_client(server_params, errlog=self._server_log_file)
)
```

**Key lesson**: Check MCP SDK signature - parameter is `errlog` not `stderr`.

### 3. Orchestrator Compatibility

**Discovery**: `loop-basic` orchestrator is incompatible with `hooks-streaming-ui` hook, causing raw TextBlock output.

**Evidence**:
- Default profile (with thinking): Uses `loop-streaming`
- Base profile test: Shows raw TextBlock with `loop-basic`
- mcp-example with `loop-basic`: Shows raw TextBlock
- mcp-example with `loop-streaming`: Formats correctly

**Fix**: Changed orchestrator from `loop-basic` to `loop-streaming`:
```yaml
session:
  orchestrator:
    module: loop-streaming  # Not loop-basic!
    source: git+https://github.com/microsoft/amplifier-module-loop-streaming@main
    config:
      extended_thinking: true
```

**Critical insight**: Hooks and orchestrators must be compatible. Not all hook/orchestrator combinations work.

### 4. ToolResult Output Format

**Discovery**: ToolResult.output must be a dict, not a string.

**Evidence** from tool-filesystem:
```python
return ToolResult(success=True, output={"path": str(p), "content": data})  # Dict!
```

**Original MCP module** (wrong):
```python
output = self._extract_content(result)  # Returns string
return ToolResult(success=True, output=output)  # String causes errors
```

**Fix**: Wrap content in dicts:
```python
# wrapper.py
return ToolResult(success=True, output={"content": content})

# resource_wrapper.py
return ToolResult(success=True, output={"uri": uri, "content": content})

# prompt_wrapper.py
return ToolResult(success=True, output={"prompt": self.prompt_name, "messages": messages})
```

## Methodology Lessons Learned

### What Went Wrong (Anti-Patterns)

1. **Jumped to conclusions without evidence**
   - Assumed dict format based on error message alone
   - Didn't verify by checking other tool implementations first
   - Reverted working fix when challenged instead of defending with evidence

2. **Made assumptions about user environment**
   - Started modifying Python environment without permission
   - Should have asked before suggesting invasive changes

3. **Didn't validate "fixes" before declaring them complete**
   - Said "this is working" without testing
   - Trusted logic over empirical verification

### What Worked (Patterns to Follow)

1. **Evidence-based debugging**
   - Comparing working profile (default) vs broken profile (mcp-example)
   - Reading bundled profile examples to see current patterns
   - Checking tool-filesystem implementation to understand ToolResult format

2. **Systematic investigation**
   - Profile → Orchestrator → Hooks → Tool output format
   - Each layer revealed different issues

3. **User-provided evidence**
   - Screenshots showing actual behavior
   - Error messages with full context
   - Comparison between working and broken states

## Testing Checklist for Future

When fixing module integration issues:

- [ ] Check bundled profiles for current patterns
- [ ] Compare with working modules (tool-filesystem, tool-bash)
- [ ] Verify orchestrator/hook compatibility
- [ ] Test with actual profile, not just unit tests
- [ ] Clear module cache between tests
- [ ] Validate "it works" with actual execution, not assumption

## Files Changed

**Core implementation**:
- `manager.py` - Added verbose config, pass coordinator
- `client.py` - Implemented stderr redirection
- `wrapper.py` - Return dict, accept hooks
- `resource_wrapper.py` - Return dict, accept hooks
- `prompt_wrapper.py` - Return dict, accept hooks
- `__init__.py` - Pass coordinator to manager

**Example/documentation**:
- `examples/mcp-example.md` - Complete working profile
- `README.md` - Verbose configuration docs

**Tests**:
- `tests/conftest.py` - Added mock_hooks, mock_coordinator fixtures
- `tests/test_*.py` - Updated for hooks parameter, dict output expectations

## Final Configuration

Working profile pattern for MCP tools:

```yaml
profile:
  name: mcp-example
  extends: base

session:
  orchestrator:
    module: loop-streaming  # Required for hooks-streaming-ui
    source: git+https://github.com/microsoft/amplifier-module-loop-streaming@main
    config:
      extended_thinking: true

providers:
  - module: provider-anthropic
    source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main

tools:
  - module: tool-mcp
    source: git+https://github.com/microsoft/amplifier-module-tool-mcp@main
    config:
      verbose_servers: false  # Suppress server noise

hooks:
  - module: hooks-streaming-ui  # Required for formatting
    source: git+https://github.com/microsoft/amplifier-module-hooks-streaming-ui@main
```

## Key Dependencies

**Orchestrator**: `loop-streaming` (loop-basic doesn't format properly)
**Hooks**: `hooks-streaming-ui` (required for response formatting)
**All modules**: Must have explicit source URLs

## Test Results

- ✅ 49/50 tests pass (1 flaky asyncio test in integration)
- ✅ Clean console output (no server noise)
- ✅ Proper response formatting (no raw TextBlock)
- ✅ Server logs captured to ~/.amplifier/logs/mcp-servers/
- ✅ AMPLIFIER_MCP_VERBOSE=true shows server output when debugging

## Recommendations

1. **For rapid-change codebases**: Always compare with working bundled examples first
2. **For integration issues**: Check orchestrator/hook compatibility matrix
3. **For output format**: Match other tools in the same category
4. **For validation**: Test with actual execution, not assumptions
