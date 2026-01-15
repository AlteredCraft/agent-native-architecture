# ==THIS DOC IS ON HOLD== 
Still ideating on the approach to memory management improvements.


# Memory Management Enhancement Plan

> Pulled from `docs/current-notes.md` "DO NEXT: review the management of memory"

## Goal

Improve the agent's memory system to prevent "things getting lost" - add update/delete capabilities, address key proliferation through prompt guidance, and enable exact key lookups for CRUD operations.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Memory CRUD | Add `update_memory` + `delete_memory` tools | Agent needs to correct and remove outdated memories |
| Key taxonomy | System prompt guidance (not enforced in code) | Fits ANA philosophy - agent reasons about structure |
| Query interface | Keep simple, add exact key lookup for CRUD | Avoid exposing ChromaDB operator complexity |

## Current State

### What We Have
- `store_memory(key, value)` - append-only, always succeeds
- `recall_memory(query, limit)` - semantic search only
- No exact key lookup, no update, no delete

### Problems
1. **Duplicates accumulate** - storing same key twice creates two memories
2. **Can't correct mistakes** - no way to update incorrect information
3. **Tag proliferation** - no guidance leads to `user-pref`, `user-display-pref`, etc.
4. **No deduplication check** - agent can't verify "do I already know this?"

## ChromaDB Capabilities

### Available (from [docs](https://docs.trychroma.com/docs/querying-collections/metadata-filtering))
| Feature | Operators |
|---------|-----------|
| Metadata filtering | `$eq`, `$gt`, `$gte`, `$lte`, `$in`, `$nin`, `$and`, `$or` |
| Full-text search | `$contains`, `$not_contains`, `$regex`, `$not_regex` |
| Exact key lookup | `where={"key": "exact_value"}` |

### What We'll Use
- **Exact key lookup** for update/delete operations
- Keep semantic search as primary recall mechanism
- Don't expose operator syntax to agent (too complex, not ANA-aligned)

---

## Implementation Tasks

### 1. Add `_get_memory_by_key()` helper (internal)
**File:** `agent_native_app/tools.py`

```python
def _get_memory_by_key(key: str) -> Item | None:
    """Get a memory by exact key match."""
    results = _memory_store.query(where={"key": key}, limit=1)
    return results[0] if results else None
```

### 2. Add `update_memory` tool
**File:** `agent_native_app/tools.py`

```python
@log_tool_call
def update_memory(key: str, value: Any) -> dict | None:
    """
    Update an existing memory by key.

    Args:
        key: The exact key of the memory to update
        value: The new value

    Returns:
        The updated memory, or None if key not found.
    """
    existing = _get_memory_by_key(key)
    if not existing:
        return None

    content = f"{key}: {value}" if not isinstance(value, str) else value
    updated = _memory_store.update(
        existing.id,
        content=content,
        metadata={"key": key, "value_type": type(value).__name__}
    )
    return {"key": key, "content": updated.content, "updated_at": updated.updated_at}
```

Add to `TOOLS` dict and `TOOL_SCHEMAS`.

### 3. Add `delete_memory` tool
**File:** `agent_native_app/tools.py`

```python
@log_tool_call
def delete_memory(key: str) -> bool:
    """
    Delete a memory by key.

    Args:
        key: The exact key of the memory to delete

    Returns:
        True if deleted, False if not found.
    """
    existing = _get_memory_by_key(key)
    if not existing:
        return False
    return _memory_store.delete(existing.id)
```

Add to `TOOLS` dict and `TOOL_SCHEMAS`.

### 4. Enhance system prompt with memory guidance
**File:** `agent_native_app/prompts/system.md`

Replace "How to Use Memory" section:

```markdown
## How to Use Memory

### When to Store
Store memories when you learn something persistent:
- User preferences ("prefers deep work in mornings")
- Project context ("Acme is high priority this quarter")
- Personal patterns ("picks up kids at 3pm weekdays")
- Your observations ("user often reschedules Monday tasks")

### Key Naming Convention
Use hierarchical, descriptive keys to avoid proliferation:

| Category | Pattern | Example |
|----------|---------|---------|
| Preferences | `pref.<domain>.<detail>` | `pref.scheduling.deep_work_time` |
| Context | `context.<domain>` | `context.project.acme` |
| Patterns | `pattern.<what>` | `pattern.reschedules_mondays` |
| Facts | `fact.<what>` | `fact.kids_pickup_time` |

**Good:** `pref.display.theme` (reusable, findable)
**Bad:** `user-display-pref` (vague, hard to update later)

### Memory Lifecycle
- **Before storing**: Recall to check if a related memory exists
- **Update** when preferences change (don't create duplicates)
- **Delete** when information is no longer valid
- **Consolidate** when you notice fragmented related memories

### Recall Strategically
Recall memories when they might inform your response:
- User asks about scheduling → recall scheduling preferences
- Working on a project → recall project context
- Giving recommendations → recall relevant patterns
```

### 5. Update docs/current-notes.md
Remove the completed "DO NEXT" item about memory management.

---

## Files to Modify

| File | Changes |
|------|---------|
| `agent_native_app/tools.py` | Add `_get_memory_by_key`, `update_memory`, `delete_memory`, update `TOOLS` and `TOOL_SCHEMAS` |
| `agent_native_app/prompts/system.md` | Expand "How to Use Memory" section |
| `docs/current-notes.md` | Remove completed TODO |

---

## Deferred / Future Considerations

- **Memory decay**: Weight recent memories higher in recall
- **Consolidation tool**: Agent-triggered merge of related memories
- **Confidence scores**: Track certainty of stored inferences
- **Source attribution**: Link memories to conversations that produced them
- **Expose advanced queries**: If simple interface proves insufficient
- **Tags management mechanism**: A way for the agent to discover what keys/tags exist and query them hierarchically. Could integrate with the key naming convention:
  ```
  list_memory_keys()                    → all keys
  list_memory_keys(prefix="pref.")      → ["pref.scheduling.deep_work_time", "pref.display.theme", ...]
  list_memory_keys(prefix="pref.scheduling.*")  → keys under that namespace
  ```
  This would help the agent understand "what do I know?" before storing/recalling, reducing duplicates and enabling better consolidation. *Needs more thought on API design and whether it's worth the complexity.*
