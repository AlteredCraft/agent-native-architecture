# Agent Native Architectures

An experiment in building software where the LLM is the core, not an add-on.

## The Idea

Classical apps are **schema-first**: you define data models, build features, then maybe add AI. The schema dictates what's possible.

This project inverts that. It's **semantic-first**: the LLM's understanding of language is the core. Structured data becomes an *output* of understanding, not an *input* required from users.

We're using a todo/personal assistant as a familiar example to explore what this means in practice.

## Quick Start

```bash
# Clone and enter
cd agent-native-todo

# Install dependencies
uv sync

# Copy example env and configure
cp .env.example .env
# Edit .env with your API key (get one at https://openrouter.ai/keys)

# Run
uv run python main.py
```

## What You Can Do

Talk naturally:

```
You: Add a task to review the quarterly report
Assistant: Created a task: "review the quarterly report"

You: I prefer to do deep work in the morning
Assistant: I'll remember that you prefer deep work in the morning.

You: What should I focus on today?
Assistant: Based on your preference for morning deep work,
          I'd suggest tackling the quarterly report review first...
```

The assistant has 7 primitive tools and builds everything else through reasoning:

| Tool | Purpose |
|------|---------|
| `create_item` | Store anything (task, note, idea, reminder) |
| `update_item` | Modify content or properties |
| `delete_item` | Remove |
| `query_items` | Find by meaning or properties |
| `get_time` | Temporal awareness |
| `store_memory` | Remember preferences and patterns |
| `recall_memory` | Retrieve relevant memories |

Higher-level concepts (projects, priorities, contexts) emerge from reasoning, not from baking them into the tool layer.

## Architecture

```
┌─────────────────────────────────────────┐
│                  CLI                    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              LLM Agent                  │
│        (OpenRouter, any model)          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           7 Primitive Tools             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Store (Protocol)               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│             ChromaDB                    │
│     (items + memory, semantic search)   │
└─────────────────────────────────────────┘
```

## The Experiment: ChromaDB Only

We're testing whether a vector database can serve as the *single* persistence layer.

**Traditional approach:**
- SQLite for structured data
- Vector DB for embeddings
- Two systems to sync

**Our experiment:**
- ChromaDB stores everything
- Every item is semantically searchable by default
- "Find tasks similar to this" just works

**Tradeoffs we're accepting:**
- Flat metadata (no nested objects)
- Less battle-tested for CRUD
- Embedding cost for every item

**What we hope to gain:**
- Semantic search on items for free
- Simpler architecture
- Natural language queries everywhere

**The hedge:** We built behind an abstract `Store` protocol. If ChromaDB doesn't work, we can swap to SQLite without touching tools or agent code.

## Project Structure

```
agent_native_app/
├── config.py         # Configuration from .env
├── logging_config.py # Central logging setup
├── store.py          # Store protocol + ChromaStore
├── tools.py          # 7 primitives + OpenAI-compatible schemas
├── agent.py          # OpenRouter agent with tool calling
├── cli.py            # Interactive REPL
└── prompts/
    └── system.md     # "How to think" prompt
```
agent_native_app/
├── config.py         # Configuration from .env
├── logging_config.py # Central logging setup
├── store.py          # Store protocol + ChromaStore
├── tools.py          # 7 primitives + OpenAI-compatible schemas
├── agent.py          # OpenRouter agent with tool calling
├── cli.py            # Interactive REPL
└── prompts/
    └── system.md     # "How to think" prompt

scripts/
└── db_describe.py    # Inspect ChromaDB collections

docs/
├── blog-post-the-app-is-dead.md   # Philosophy essay
├── implementation-plan.md          # Technical design
└── research-notes.md               # Background research
```

## Configuration

Configuration is managed via `.env` file (copy from `.env.example`):

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key ([get one here](https://openrouter.ai/keys)) |
| `OPENROUTER_MODEL` | Model to use (e.g., `anthropic/claude-sonnet-4`) |
| `LOG_LEVEL_APP` | Log level for app code (DEBUG, INFO, WARNING, ERROR) |
| `LOG_LEVEL_DEPS` | Log level for dependencies (default: INFO) |
| `LOG_TO_CONSOLE` | Whether to log to stderr (true/false) |
| `LOG_FILE_PATH` | Path to log file (e.g., `logs/app.log`) |

**Data**: Stored in `.data/` directory (ChromaDB persistent storage) with two collections:
- `items` — Tasks, notes, reminders, ideas
- `memory` — User preferences and patterns

**Inspect the database**:
```bash
uv run python scripts/db_describe.py           # Overview
uv run python scripts/db_describe.py -s 3      # With 3 sample items per collection
```
outputs something like:
```bash
❯ uv run python scripts/db_describe.py
Database: .data
Collections: 2
============================================================

📁 Collection: memory
----------------------------------------
  Browse: chroma browse memory --path /Users/sam/Projects/agent-native-todo/.data
  Config: {'hnsw:space': 'cosine'}
  Items: 1
  Metadata fields:
    - created_at: str
    - key: str
    - updated_at: str
    - value_type: str
  key values: user_organization_preferences
  value_type values: str

📁 Collection: items
----------------------------------------
  Browse: chroma browse items --path /Users/sam/Projects/agent-native-todo/.data
  Config: {'hnsw:space': 'cosine'}
  Items: 6
  Metadata fields:
    - context: str
    - created_at: str
    - due_date: str
    - parent_task: str
    - priority: int
    - priority_display: str
    - project: str
    - status: str
    - type: str
    - updated_at: str
  type values: task
  status values: active, in-progress
  priority values: 2

============================================================
Chroma CLI: https://docs.trychroma.com/docs/cli/install
```

## Philosophy

The system prompt teaches the assistant *how to think*, not *what to do*:

- Items are flexible containers, not rigid task records
- Properties emerge from context (type, status, priority, project...)
- Memory learns user patterns over time
- Explain reasoning, but don't be verbose
- Ask clarifying questions rather than guess
- Be an advisor, not an autocrat

## Related

- [The App is Dead, Long Live the Assistant](docs/blog-post-the-app-is-dead.md) — Philosophy essay
- [Implementation Plan](docs/implementation-plan.md) — Technical design
- [Research Notes](docs/research-notes.md) — Background research and citations

---

## Appendix: How Tools Are Communicated to the LLM

The agent uses the **OpenAI function calling format** to communicate tools to the LLM.

### Tool Schema Definition

Each tool is defined as a JSON schema in `agent_native_app/tools.py`:

```python
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "create_item",
            "description": "Create a new item...",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "..."},
                    "properties": {"type": "object", "description": "..."}
                },
                "required": ["content"]
            }
        }
    },
    # ... 6 more tools
]
```

A separate `TOOLS` dictionary maps names to Python functions for execution:

```python
TOOLS = {
    "create_item": create_item,
    "update_item": update_item,
    # ...
}
```

### Passing Tools to the LLM

In `agent_native_app/agent.py`, tools are sent on every API call:

```python
response = self._client.chat.completions.create(
    model=self._model,
    messages=messages,
    tools=TOOL_SCHEMAS,  # All 7 tool schemas
    tool_choice="auto"   # LLM decides when to use them
)
```

### The Agentic Loop

```
User Input
    │
    ▼
┌─────────────────────────────────┐
│  API Call                       │
│  - System prompt                │
│  - Message history              │
│  - Tool schemas                 │◄──────────────┐
└───────────────┬─────────────────┘               │
                │                                 │
                ▼                                 │
        LLM Response                              │
                │                                 │
        ┌───────┴───────┐                         │
        │               │                         │
   Has tool_calls?  No tool_calls                 │
        │               │                         │
        ▼               ▼                         │
   Execute tools    Return content                │
        │           (done)                        │
        ▼                                         │
   Add results as                                 │
   "tool" messages ───────────────────────────────┘
```

When the LLM wants to use a tool, it returns a `tool_calls` array. The agent:

1. Parses each tool call (name + JSON arguments)
2. Looks up the function in `TOOLS`
3. Executes it: `TOOLS[name](**arguments)`
4. Appends the result as a `"role": "tool"` message
5. Loops back to the LLM with updated history

The loop continues until the LLM responds with content and no tool calls.

### Message History Format

```python
messages = [
    {"role": "system", "content": "..."},           # How to think
    {"role": "user", "content": "Add a task..."},   # User input
    {"role": "assistant", "tool_calls": [...]},     # LLM requests tool
    {"role": "tool", "tool_call_id": "...",         # Tool result
     "content": "{\"id\": \"abc123\", ...}"},
    {"role": "assistant", "content": "Created..."}  # Final response
]
```

This is the standard OpenAI tool calling protocol, which works with any compatible API (OpenRouter, OpenAI, Anthropic via adapters, etc.).

## License

MIT
