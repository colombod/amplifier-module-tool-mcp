"""Content extraction utilities with size protection."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default maximum content size in characters (~12k tokens at 4 chars/token)
DEFAULT_MAX_CONTENT_SIZE = 50_000

# Truncation notice template
TRUNCATION_NOTICE = "\n\n[... Content truncated due to size. Total: {total:,} chars, Showing: {shown:,} chars. Use smaller queries or request specific sections ...]"


def truncate_content_if_needed(
    content: str,
    max_size: int,
    context_info: str = "",
) -> tuple[str, bool]:
    """
    Truncate content if it exceeds maximum size.

    Args:
        content: Raw content string
        max_size: Maximum allowed size in characters
        context_info: Additional context for logging (e.g., "tool: my_tool")

    Returns:
        Tuple of (content, was_truncated)
    """
    if len(content) <= max_size:
        return content, False

    # Content exceeds limit - truncate and warn
    truncated = content[:max_size]
    notice = TRUNCATION_NOTICE.format(
        total=len(content),
        shown=max_size,
    )

    # Log warning with context
    log_msg = f"Content truncated: {len(content):,} chars → {max_size:,} chars"
    if context_info:
        log_msg = f"{context_info}: {log_msg}"
    logger.warning(log_msg)

    return truncated + notice, True


def extract_text_from_mcp_content(content_items: Any) -> str:
    """
    Extract text from MCP content items (handles various MCP formats).

    Args:
        content_items: MCP content items (list or single item)

    Returns:
        Extracted text string
    """
    if isinstance(content_items, list):
        # Join multiple content items
        parts = []
        for item in content_items:
            if hasattr(item, "text"):
                parts.append(str(item.text))
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    
    # Single item
    if hasattr(content_items, "text"):
        return str(content_items.text)
    
    return str(content_items)


def extract_text_from_mcp_resource(content_items: Any) -> str:
    """
    Extract text from MCP resource contents (handles text and binary).

    Args:
        content_items: MCP resource contents (list or single item)

    Returns:
        Extracted text string
    """
    if isinstance(content_items, list):
        # Join multiple content items
        parts = []
        for item in content_items:
            if hasattr(item, "text"):
                parts.append(str(item.text))
            elif hasattr(item, "blob"):
                # Binary content - indicate size
                blob_size = len(item.blob) if hasattr(item.blob, "__len__") else "unknown"
                parts.append(f"[Binary content: {blob_size} bytes]")
            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif "blob" in item:
                    blob_size = len(item["blob"]) if hasattr(item["blob"], "__len__") else "unknown"
                    parts.append(f"[Binary content: {blob_size} bytes]")
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    
    # Single item
    if hasattr(content_items, "text"):
        return str(content_items.text)
    if hasattr(content_items, "blob"):
        blob_size = len(content_items.blob) if hasattr(content_items.blob, "__len__") else "unknown"
        return f"[Binary content: {blob_size} bytes]"
    
    return str(content_items)
