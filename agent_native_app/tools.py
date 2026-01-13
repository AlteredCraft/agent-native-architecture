"""
Tool definitions for the AI assistant.

These are the primitives the LLM can use. Higher-level concepts
(projects, priorities, contexts) emerge from reasoning, not from
baking them into tools.
"""

import functools
import logging
from typing import Any, Callable

from .store import ChromaStore

logger = logging.getLogger(__name__)


def log_tool_call(func: Callable) -> Callable:
    """Decorator to log tool calls with params and output."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"🧰 Tool call: {func.__name__}")
        logger.debug(f"  Params: {kwargs}")
        result = func(*args, **kwargs)
        logger.debug(f"  Result: {result}")
        return result
    return wrapper


# Initialize stores
_items_store = ChromaStore(collection_name="items", persist_dir=".data")
_gc_store = ChromaStore(collection_name="global_context", persist_dir=".data")

# Global Context constants
GC_ITEM_ID = "global_context"


# ============================================================================
# Item Operations
# ============================================================================

@log_tool_call
def create_item(content: str, properties: dict[str, Any] | None = None) -> dict:
    """
    Create a new item with content and optional properties.

    Args:
        content: The item's text content (task description, note, etc.)
        properties: Optional metadata (e.g., {"type": "task", "status": "active"})

    Returns:
        The created item with id, content, properties, and timestamps.
    """
    item = _items_store.add(content, properties)
    return {
        "id": item.id,
        "content": item.content,
        "properties": item.metadata,
        "created_at": item.created_at,
        "updated_at": item.updated_at
    }


@log_tool_call
def update_item(
    id: str,
    content: str | None = None,
    properties: dict[str, Any] | None = None
) -> dict | None:
    """
    Update an existing item's content and/or properties.

    Args:
        id: The item's unique identifier
        content: New content (optional, keeps existing if not provided)
        properties: Properties to update (merged with existing)

    Returns:
        The updated item, or None if not found.
    """
    item = _items_store.update(id, content, properties)
    if not item:
        return None
    return {
        "id": item.id,
        "content": item.content,
        "properties": item.metadata,
        "created_at": item.created_at,
        "updated_at": item.updated_at
    }


@log_tool_call
def delete_item(id: str) -> bool:
    """
    Delete an item by ID.

    Args:
        id: The item's unique identifier

    Returns:
        True if deleted, False if not found.
    """
    return _items_store.delete(id)


@log_tool_call
def query_items(
    text: str | None = None,
    where: dict[str, Any] | None = None,
    limit: int = 10
) -> list[dict]:
    """
    Query items by semantic similarity and/or property filters.

    Args:
        text: Semantic search query (finds similar items by meaning)
        where: Property filter (e.g., {"status": "active", "type": "task"})
        limit: Maximum number of results

    Returns:
        List of matching items.
    """
    items = _items_store.query(text, where, limit)
    return [
        {
            "id": item.id,
            "content": item.content,
            "properties": item.metadata,
            "created_at": item.created_at,
            "updated_at": item.updated_at
        }
        for item in items
    ]


# ============================================================================
# Global Context
# ============================================================================

def _load_gc_lines() -> list[str]:
    """Load Global Context and split into lines."""
    item = _gc_store.get(GC_ITEM_ID)
    if not item:
        return []
    return item.content.split("\n")


def _save_gc_lines(lines: list[str]) -> None:
    """Join lines and save Global Context."""
    content = "\n".join(lines)
    _gc_store.upsert(GC_ITEM_ID, content, {"item_type": "global_context"})


def _format_gc_for_display(lines: list[str]) -> str:
    """Format with line numbers for system prompt injection."""
    if not lines or all(line == "" for line in lines):
        return "(empty - populate as you learn about the user)"
    return "\n".join(f"{i}-- {line}" for i, line in enumerate(lines) if line)


def _compact_gc(text: str) -> str:
    """Remove empty lines between sessions."""
    import re
    return re.sub(r'\n{2,}', '\n', text).strip()


@log_tool_call
def append_context(content: str) -> dict:
    """
    Add a new line to Global Context.

    Use this to record persistent knowledge about the user: preferences,
    patterns, constraints, or observations that should shape future reasoning.

    Args:
        content: The knowledge to add (e.g., "Prefers deep work in mornings")

    Returns:
        Confirmation with the new line number.
    """
    lines = _load_gc_lines()
    lines.append(content)
    _save_gc_lines(lines)
    return {"line": len(lines) - 1, "content": content}


@log_tool_call
def replace_context(line: int, content: str) -> dict | None:
    """
    Update an existing line in Global Context.

    Use this when knowledge needs to be corrected or refined.

    Args:
        line: The line number to update (0-indexed)
        content: The new content for this line

    Returns:
        Confirmation with old and new content, or None if line not found.
    """
    lines = _load_gc_lines()
    if line < 0 or line >= len(lines):
        return None
    old_content = lines[line]
    lines[line] = content
    _save_gc_lines(lines)
    return {"line": line, "old_content": old_content, "new_content": content}


@log_tool_call
def delete_context(line: int) -> dict | None:
    """
    Remove a line from Global Context.

    The line is replaced with an empty string during the session to keep
    indices stable. Empty lines are compacted at the start of the next session.

    Args:
        line: The line number to remove (0-indexed)

    Returns:
        Confirmation with deleted content, or None if line not found.
    """
    lines = _load_gc_lines()
    if line < 0 or line >= len(lines):
        return None
    deleted_content = lines[line]
    lines[line] = ""  # Replace with empty, compacted between sessions
    _save_gc_lines(lines)
    return {"line": line, "deleted_content": deleted_content}


# ============================================================================
# Tool Registry (for LLM integration)
# ============================================================================

TOOLS = {
    "create_item": create_item,
    "update_item": update_item,
    "delete_item": delete_item,
    "query_items": query_items,
    "append_context": append_context,
    "replace_context": replace_context,
    "delete_context": delete_context,
}

# Tool schemas for OpenAI-compatible function calling
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "create_item",
            "description": "Create a new item (task, note, reminder, idea, etc.) with content and optional properties. Use this when the user wants to add something to track.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The item's text content (task description, note, etc.)"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Optional metadata like type, status, due_date, priority, project, tags, etc.",
                        "additionalProperties": True
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_item",
            "description": "Update an existing item's content and/or properties. Use this to modify, complete, or change items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The item's unique identifier"
                    },
                    "content": {
                        "type": "string",
                        "description": "New content (optional)"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties to update (merged with existing)",
                        "additionalProperties": True
                    }
                },
                "required": ["id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_item",
            "description": "Delete an item permanently. Use when the user wants to remove something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The item's unique identifier"
                    }
                },
                "required": ["id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_items",
            "description": "Search for items by semantic similarity (meaning) and/or property filters. Use this to find, list, or retrieve items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Semantic search query - finds items with similar meaning"
                    },
                    "where": {
                        "type": "object",
                        "description": "Property filter (e.g., {\"status\": \"active\", \"type\": \"task\"})",
                        "additionalProperties": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 10)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_context",
            "description": "Add a new line to Global Context. Use this to record persistent knowledge about the user: preferences, patterns, constraints, or observations that should shape all future reasoning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The knowledge to add (e.g., 'Prefers deep work in mornings')"
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "replace_context",
            "description": "Update an existing line in Global Context. Use this when knowledge needs to be corrected or refined.",
            "parameters": {
                "type": "object",
                "properties": {
                    "line": {
                        "type": "integer",
                        "description": "The line number to update (0-indexed, as shown in Global Context)"
                    },
                    "content": {
                        "type": "string",
                        "description": "The new content for this line"
                    }
                },
                "required": ["line", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_context",
            "description": "Remove a line from Global Context. Use this when knowledge is no longer relevant. Line indices remain stable during the session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "line": {
                        "type": "integer",
                        "description": "The line number to remove (0-indexed, as shown in Global Context)"
                    }
                },
                "required": ["line"]
            }
        }
    }
]
