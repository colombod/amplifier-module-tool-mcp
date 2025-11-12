# Content Size Protection - Implementation Summary

**Date**: 2025-11-11  
**Issue**: MCP servers returning excessive content causing session crashes due to context exhaustion  
**Solution**: Automatic content size limits with truncation and warning logs

---

## What Was Implemented

### 1. Core Protection Utilities (`content_utils.py`)

New module with:
- **DEFAULT_MAX_CONTENT_SIZE**: 50,000 characters (~12k tokens at 4 chars/token)
- **truncate_content_if_needed()**: Smart truncation with clear messaging
- **extract_text_from_mcp_content()**: Content extraction from various MCP formats
- **extract_text_from_mcp_resource()**: Resource extraction with binary content handling

### 2. Configuration Support (`manager.py`)

- Reads `max_content_size` from module config (default: 50,000)
- Passes limit to all wrappers during initialization
- Logs the configured limit at startup

### 3. Protection in All Wrappers

Updated **wrapper.py**, **resource_wrapper.py**, and **prompt_wrapper.py** to:
- Accept `max_content_size` parameter in constructor
- Apply size limits before returning content
- Add metadata to output: `content_size_chars` and `content_truncated`
- Log warnings when truncation occurs

---

## How It Works

### Automatic Truncation

When content exceeds the limit:

```
Original content: 60,000 characters
↓ (truncate_content_if_needed)
Truncated to: 50,000 characters
+ Truncation notice appended
↓
Final result: 50,135 characters (with notice)
```

**Truncation Notice Format**:
```
[... Content truncated due to size. Total: 60,000 chars, Showing: 50,000 chars. 
Use smaller queries or request specific sections ...]
```

### Warning Logs

When truncation occurs, a warning is logged:

```
WARNING:amplifier_module_tool_mcp.content_utils:MCP tool 'mcp_server_tool': 
Content truncated: 60,000 chars → 50,000 chars
```

This helps you identify which MCP tools are returning large content.

### Metadata in Output

Every tool result now includes:

```python
ToolResult(
    success=True,
    output={
        "content": "...",
        "mcp_server": "my-server",
        "mcp_tool": "my-tool",
        "content_size_chars": 50135,      # ← New
        "content_truncated": True,         # ← New
    }
)
```

---

## Configuration

### Default Behavior (No Config Needed)

Out of the box, all MCP content is limited to 50,000 characters.

### Custom Limit

In your profile:

```yaml
tools:
  - module: tool-mcp
    config:
      max_content_size: 100000  # Increase to 100k chars (~25k tokens)
```

### Recommended Values

| Use Case | Recommended Limit | Tokens (approx) |
|----------|-------------------|-----------------|
| **Default** | 50,000 chars | ~12k tokens |
| **Large contexts** | 100,000 chars | ~25k tokens |
| **Conservative** | 25,000 chars | ~6k tokens |
| **Unrestricted** | 1,000,000 chars | ~250k tokens (⚠️ risk) |

**Note**: Be cautious with very large limits - they can still cause session crashes if multiple large results are returned.

---

## Monitoring Content Size

### Check Logs for Truncation Warnings

```bash
# View server logs (if verbose_servers: false)
cat ~/.amplifier/logs/mcp-servers/my-server.log

# View Amplifier logs
# Look for: "Content truncated: X chars → Y chars"
```

### In Log Viewer

With `hooks-logging` enabled, you can see:
- `content_size_chars`: Actual size of content returned
- `content_truncated`: Whether truncation occurred

Example event in log viewer:
```json
{
  "event": "tool:post",
  "data": {
    "tool_name": "mcp_repomix_generate",
    "tool_result": {
      "output": {
        "content_size_chars": 50135,
        "content_truncated": true,
        "mcp_server": "repomix",
        "mcp_tool": "generate"
      }
    }
  }
}
```

---

## Testing

### Unit Tests

All existing tests pass (50/50):
```bash
cd amplifier-module-tool-mcp
uv run pytest tests/ -v
```

### Manual Verification

The content protection was tested with:
- ✅ Large content (60k chars) → truncated to 50k
- ✅ Custom limits (30k) → truncated correctly
- ✅ Small content (<50k) → no truncation
- ✅ Warning logs emitted → correct format

---

## What This Fixes

### Before (Problem)

1. MCP server returns 50MB file content
2. All 50MB injected into context
3. Context window exceeded
4. **Session crashes** ❌

### After (Solution)

1. MCP server returns 50MB file content
2. Content automatically truncated to 50k chars
3. Truncation notice added explaining what happened
4. Warning logged for monitoring
5. **Session continues** ✅

---

## Example Output

### When Content is Truncated

```
Tool: mcp_repomix_generate
Result: 
Here is the codebase summary...
[thousands of lines of code]
...more code...

[... Content truncated due to size. Total: 125,000 chars, Showing: 50,000 chars. 
Use smaller queries or request specific sections ...]
```

### When Content is Under Limit

```
Tool: mcp_zen_codereview
Result:
This code looks good. Here are a few suggestions:
1. Consider adding error handling
2. Add type hints
3. Write unit tests

(No truncation notice - content was under limit)
```

---

## Migration Notes

### No Breaking Changes

- All existing code continues to work
- Default behavior is safe (50k limit)
- No configuration required

### Backward Compatible

- Old wrappers without `max_content_size` parameter would fail
- New wrappers handle missing parameter gracefully (defaults to 50k)

### If You Need Unlimited Content

**Not recommended**, but if absolutely necessary:

```yaml
tools:
  - module: tool-mcp
    config:
      max_content_size: 10000000  # 10 million chars (~2.5M tokens)
```

⚠️ **Warning**: This defeats the protection and may cause crashes.

---

## Files Changed

1. **NEW**: `amplifier_module_tool_mcp/content_utils.py` - Core utilities
2. **UPDATED**: `amplifier_module_tool_mcp/manager.py` - Config reading
3. **UPDATED**: `amplifier_module_tool_mcp/wrapper.py` - Tool protection
4. **UPDATED**: `amplifier_module_tool_mcp/resource_wrapper.py` - Resource protection
5. **UPDATED**: `amplifier_module_tool_mcp/prompt_wrapper.py` - Prompt protection
6. **UPDATED**: `README.md` - Documentation

---

## Next Steps (Optional Enhancements)

### Short-term (Not Implemented Yet)

- [ ] Content type detection (detect images, JSON, etc.)
- [ ] Smart truncation at line boundaries
- [ ] Compression for structured data

### Long-term (Future)

- [ ] Streaming support for large content
- [ ] Chunked reading with pagination
- [ ] Configurable per-server limits
- [ ] Per-tool override configuration

---

## Questions?

**Q: Will this break existing MCP tools?**  
A: No, it's backward compatible. Existing tools will get the default 50k limit.

**Q: Can I disable truncation?**  
A: Set a very high limit (e.g., 10M chars), but this is not recommended.

**Q: How do I know if content was truncated?**  
A: Check logs for warnings or inspect `content_truncated` field in output.

**Q: What if I need the full content?**  
A: Options:
1. Ask MCP tool for a specific section
2. Use filters/queries to reduce content
3. Increase `max_content_size` (with caution)
4. Process content in chunks (future enhancement)

**Q: Does this affect performance?**  
A: Minimal - truncation is a simple string slice operation.

---

## Summary

✅ **Implemented**: Automatic content size protection  
✅ **Default**: 50,000 character limit (~12k tokens)  
✅ **Configurable**: Set via `max_content_size` in profile  
✅ **Observable**: Warning logs + metadata in output  
✅ **Tested**: All 50 tests pass + manual verification  
✅ **Documented**: README updated with configuration  

**This should resolve your session-killing issue caused by MCP servers returning excessive context.**
