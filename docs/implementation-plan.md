# Agent-Native Todo: Implementation Plan

## Premise

### What We're Exploring
This is an experiment in **agent-native application design** — building a personal assistant
where the LLM is the core, not an add-on. We're testing whether the classical approach
to app development (schema-first, deterministic, feature-bound) can be inverted.

**The classical approach**: Define data models → Build features → Add AI as enhancement
**Our approach**: Define minimal primitives → Let LLM reasoning emerge → Structure as output

We're using a todo/personal assistant as a familiar, discrete example to explore
these ideas concretely.

### Core Philosophy
- **Semantic-first, not schema-first**: The LLM's understanding of language and context
  is the core. Structured data becomes an *output* of understanding, not an *input*
  required from the user.
- **Primitives over prescriptions**: Tools are low-level building blocks. Higher-level
  concepts (projects, priorities, contexts) emerge from the assistant's reasoning and
  system prompt guidance — not baked into the tool layer.
- **Philosophy tested by experiment**: We validate assumptions by building, not just
  theorizing.

### The ChromaDB-Only Experiment

**The hypothesis**: A vector database (ChromaDB) can serve as the *single* persistence
layer for both structured items and semantic memory.

**Traditional approach**:
- SQLite/Postgres for structured data (tasks, properties)
- Vector DB for embeddings/semantic search
- Two systems to maintain, sync, and query

**Our experiment**:
- ChromaDB stores everything: items with metadata + memories with embeddings
- Every item becomes semantically searchable by default
- One data layer, one query interface

**Tradeoffs we're accepting**:
- ChromaDB metadata is flat (no nested objects) — we'll flatten or stringify
- Less battle-tested for CRUD than traditional databases
- Embedding every item has compute/storage cost
- May hit scaling limits we wouldn't with Postgres

**What we hope to gain**:
- Semantic search on items for free ("find tasks similar to this one")
- Simpler architecture — one store, not two
- Natural language queries over everything, not just memory
- Alignment with our "semantic-first" philosophy at the data layer

**The hedge**: We're building behind an abstract `Store` protocol. If ChromaDB
doesn't work out, we can implement `SqliteStore` without touching tools or agent code.

---

## Philosophy
Start with minimal primitives. Let the assistant's reasoning build higher-level concepts (projects, priorities, contexts) from simple building blocks. Validate through experimentation.

## Core Primitives

### Item Operations
| Tool | Signature | Purpose |
|------|-----------|---------|
| `create_item` | `(content: str, properties: dict) -> Item` | Store anything with arbitrary metadata |
| `update_item` | `(id: str, properties: dict) -> Item` | Modify any property |
| `delete_item` | `(id: str) -> bool` | Remove |
| `query_items` | `(filter: dict) -> List[Item]` | Flexible retrieval |

### Context
| Tool | Signature | Purpose |
|------|-----------|---------|
| `get_time` | `() -> datetime` | Temporal awareness |

### Memory
| Tool | Signature | Purpose |
|------|-----------|---------|
| `store_memory` | `(key: str, value: any) -> bool` | Persist user preferences, patterns, learnings |
| `recall_memory` | `(query: str) -> List[Memory]` | Semantic retrieval of relevant memories |

## Architecture (Phase 1)

```
┌─────────────────────────────────────────┐
│                  CLI                     │
│         (conversation interface)         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              LLM Agent                   │
│   (reasoning, tool selection, response)  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              Tool Layer                  │
│  (create_item, query_items, etc.)        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Store (Protocol)                │
│   abstract interface for persistence     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           ChromaStore                    │
│  (items collection + memory collection)  │
└─────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Persistence Layer
**Single store (ChromaDB) with abstract interface**

```python
# Abstract interface — easy to swap implementations later
class Store(Protocol):
    def add(self, id: str, content: str, metadata: dict) -> None: ...
    def get(self, id: str) -> Item | None: ...
    def update(self, id: str, metadata: dict) -> None: ...
    def delete(self, id: str) -> bool: ...
    def query(self, text: str | None, where: dict | None, limit: int) -> list[Item]: ...

# ChromaDB implementation
class ChromaStore(Store):
    # items collection — tasks, notes, etc.
    # memory collection — user preferences, patterns, learnings
```

**Why single store:**
- Semantic search on items for free ("find tasks like this")
- Simpler architecture
- Abstraction lets us swap to SQLite/Postgres if needed

### Step 2: Tool Definitions
- Python functions that implement each primitive
- Clean interface for LLM tool calling

### Step 3: LLM Agent
- System prompt that teaches "how to think" about task management
- OpenRouter integration for tool calling (model-agnostic)
- Conversation state management

### Step 4: CLI Interface
- Simple REPL for conversation
- Display assistant responses + any structured output

## Decisions
- **LLM Provider**: OpenRouter — model-agnostic, can swap between Claude, GPT-4, etc.
- **Embeddings/Memory**: ChromaDB (local, persistent) — semantic similarity for memory recall
- **System prompt**: Start with one comprehensive prompt, modularize if needed

## Dependencies
```
openai               # OpenRouter uses OpenAI-compatible API
chromadb             # single store for items + memory
```

## Files to Create
```
src/
├── __init__.py
├── store.py          # Store protocol + ChromaStore implementation
├── tools.py          # Tool implementations (primitives)
├── agent.py          # LLM agent (OpenRouter integration)
├── cli.py            # Terminal REPL
└── prompts/
    └── system.md     # System prompt — how to think about task management
```

## System Prompt Philosophy
The system prompt teaches the assistant *how to think*, not *what to do*:
- Understand that items are flexible (tasks, notes, reminders, ideas)
- Build concepts like "projects" or "priorities" from properties
- Use memory to learn user patterns over time
- Explain reasoning when making recommendations
- Ask clarifying questions rather than assume
