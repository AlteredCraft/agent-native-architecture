"""
Tool definitions for the AI assistant.

These are the primitives the LLM can use. Higher-level concepts
(projects, priorities, contexts) emerge from reasoning, not from
baking them into tools.
"""

import functools
import logging
from typing import Any, Callable

from .store import ChromaStore, Item

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
_memory_store = ChromaStore(collection_name="memory", persist_dir=".data")


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
# Memory
# ============================================================================

@log_tool_call
def store_memory(key: str, value: Any) -> bool:
    """
    Store a piece of information for long-term recall.

    Use this to remember user preferences, patterns, learnings, or
    any information that should persist across conversations.

    Args:
        key: A descriptive key for the memory (e.g., "user_preference_work_hours")
        value: The information to store (will be converted to string for embedding)

    Returns:
        True if stored successfully.
    """
    # Store as a document with the key as a property
    # The value is stringified as content for semantic search
    content = f"{key}: {value}" if not isinstance(value, str) else value
    _memory_store.add(content, {"key": key, "value_type": type(value).__name__})
    return True


@log_tool_call
def recall_memory(query: str, limit: int = 5) -> list[dict]:
    """
    Recall relevant memories using semantic search.

    Args:
        query: What to search for (e.g., "user's preferred work hours")
        limit: Maximum number of memories to return

    Returns:
        List of relevant memories, ordered by relevance.
    """
    items = _memory_store.query(text=query, limit=limit)
    return [
        {
            "content": item.content,
            "key": item.metadata.get("key", ""),
            "created_at": item.created_at
        }
        for item in items
    ]


# ============================================================================
# Tool Registry (for LLM integration)
# ============================================================================

TOOLS = {
    "create_item": create_item,
    "update_item": update_item,
    "delete_item": delete_item,
    "query_items": query_items,
    "store_memory": store_memory,
    "recall_memory": recall_memory,
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
            "name": "store_memory",
            "description": "Store information for long-term recall. Use this to remember user preferences, patterns, or learnings that should persist across conversations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "A descriptive key (e.g., 'user_preferred_work_hours', 'project_context_acme')"
                    },
                    "value": {
                        "type": "string",
                        "description": "The information to store"
                    }
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memory",
            "description": "Recall relevant memories using semantic search. Use this to retrieve stored preferences, patterns, or context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for (e.g., 'user work preferences')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to return (default 5)"
                    }
                },
                "required": ["query"]
            }
        }
    }
]
