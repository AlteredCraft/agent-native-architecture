# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Agent Native Architecture (ANA)** experiment: a personal assistant where the LLM is the reasoning core, not an add-on. The key inversion is that structured data is an *output* of the agent's understanding, not an *input* required from users or predetermined by developers.

See [docs/article.md](docs/article.md) for the canonical ANA definition.

## Commands

```bash
# Run the assistant
uv run python main.py

# Inspect ChromaDB collections
uv run python scripts/db_describe.py           # Overview
uv run python scripts/db_describe.py -s 3      # With sample items
```

## Architecture

```
CLI (REPL)
    ↓
Agent (OpenRouter, any model)
    ↓
6 Primitive Tools (medium-hint level)
    ↓
Store Protocol (abstract interface)
    ↓
ChromaDB (single persistence layer)
    └── items collection (tasks, notes, ideas)
    └── memory collection (user preferences, patterns)
```

### Key Design Decisions

**Single ChromaDB Store**: Rather than SQLite + vector DB, everything goes through ChromaDB. This means every item is semantically searchable by default. The `Store` protocol abstracts this—if ChromaDB proves insufficient, implementations can be swapped without touching tools or agent code.

**Medium-Hint Schema Level**: Tools are domain-agnostic (`create_item`, not `create_task`). The system prompt guides the agent on *how to think* about structure (types, statuses, priorities), but the agent decides what properties matter for each item at runtime.

**6 Primitive Tools**: `create_item`, `update_item`, `delete_item`, `query_items`, `store_memory`, `recall_memory`. Higher-level concepts emerge from agent reasoning, not from tool design.

## Code Structure

| File | Purpose |
|------|---------|
| `agent_native_app/agent.py` | LLM agent with agentic loop (calls LLM, executes tools, loops until text response) |
| `agent_native_app/store.py` | `Store` protocol + `ChromaStore` implementation |
| `agent_native_app/tools.py` | Tool implementations + OpenAI-compatible schemas in `TOOL_SCHEMAS` |
| `agent_native_app/prompts/system.md` | System prompt teaching the agent *how to think* (uses `{{today}}` placeholder) |
| `agent_native_app/cli.py` | Interactive REPL |
| `agent_native_app/config.py` | Configuration from `.env` |

## Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | API key from [openrouter.ai](https://openrouter.ai/keys) |
| `OPENROUTER_MODEL` | Model ID (e.g., `anthropic/claude-sonnet-4`) |
| `LOG_LEVEL_APP` | App log level (DEBUG shows tool calls) |

Data stored in `.data/` (ChromaDB persistent storage).

## Adding Tools

1. Add function to `agent_native_app/tools.py`
2. Add OpenAI-compatible schema to `TOOL_SCHEMAS` list
3. Register in `TOOLS` dict

The agent will automatically have access to new tools.
