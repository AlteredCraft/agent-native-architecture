# Architecture Diagrams

## ChromaDB Utilization & Agent Tool Flow

This diagram shows how the LLM agent leverages ChromaDB through the 7 primitive tools.

```mermaid
flowchart TB
    subgraph User["User Interface"]
        CLI["CLI (REPL)"]
    end

    subgraph Agent["LLM Agent"]
        LLM["OpenRouter LLM<br/>(Claude, GPT-4, etc.)"]
        SysPrompt["System Prompt<br/>'How to Think'"]
    end

    subgraph Tools["6 Primitive Tools"]
        direction LR
        subgraph ItemOps["Item Operations"]
            create["create_item()"]
            update["update_item()"]
            delete["delete_item()"]
            query["query_items()"]
        end
        subgraph MemoryOps["Memory Operations"]
            store_mem["store_memory()"]
            recall["recall_memory()"]
        end
    end

    subgraph Protocol["Store Protocol"]
        StoreAPI["Abstract Interface<br/>add() | get() | update()<br/>delete() | query()"]
    end

    subgraph ChromaDB["ChromaDB (Single Persistence Layer)"]
        subgraph ItemsCollection["items collection"]
            ItemDoc["Documents<br/>(semantic content)"]
            ItemEmbed["Embeddings<br/>(vector search)"]
            ItemMeta["Metadata<br/>type: task|note|idea<br/>status: active|done<br/>priority: int<br/>project: str<br/>due_date: str<br/>context: str<br/>created_at/updated_at"]
        end
        subgraph MemoryCollection["memory collection"]
            MemDoc["Documents<br/>(preference content)"]
            MemEmbed["Embeddings<br/>(semantic recall)"]
            MemMeta["Metadata<br/>key: str<br/>value_type: str<br/>created_at/updated_at"]
        end
    end

    CLI -->|"natural language"| LLM
    SysPrompt -.->|"guides reasoning"| LLM
    LLM -->|"tool_calls"| Tools

    create --> StoreAPI
    update --> StoreAPI
    delete --> StoreAPI
    query --> StoreAPI
    store_mem --> StoreAPI
    recall --> StoreAPI

    StoreAPI --> ItemsCollection
    StoreAPI --> MemoryCollection

    ItemDoc <--> ItemEmbed
    MemDoc <--> MemEmbed
```

### Key Design Decisions

| Aspect | How It Works |
|--------|--------------|
| **Semantic Search** | Every item gets embedded — "find similar tasks" works automatically |
| **Flat Metadata** | No nested objects (ChromaDB limitation) — properties are flattened |
| **Emergent Structure** | `type`, `status`, `project` aren't schema-enforced — LLM decides when to use them |
| **Memory Recall** | `recall_memory("deep work")` — semantic similarity finds relevant preferences |
| **The Hedge** | `Store` protocol abstracts ChromaDB — can swap to SQLite without touching tools |

### Data Flow Examples

**Creating a task:**
```
User: "Add a task to review the quarterly report"
  → LLM reasons about intent
  → Calls create_item(content="review the quarterly report", properties={type: "task", status: "active"})
  → Store.add() writes to ChromaDB items collection
  → Content embedded for future semantic search
```

**Recalling preferences:**
```
User: "What should I focus on today?"
  → LLM calls recall_memory("work preferences focus")
  → Semantic search finds "prefers deep work in the morning"
  → LLM incorporates into recommendation
```
