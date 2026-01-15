# Global Context Design

## Premise

**Global Context (GC) addresses a fundamental need independent of any specific memory implementation.** Whether the agent uses semantic search, key-value storage, or any future memory mechanism, there remains a class of knowledge that should *always be present* — not retrieved on demand, but constitutive of how the agent reasons.

This is analogous to how `CLAUDE.md` works: project context isn't queried, it's *present*. The agent doesn't ask "what are the conventions?" — it already knows because they're part of its context.

GC is a standalone enhancement that will benefit any memory architecture:
- With the current `store_memory`/`recall_memory` system
- With future Entity Context (entity-scoped reference knowledge)
- With any retrieval mechanism

The insight emerged from observing failure modes in the original memory system, but the solution transcends that specific implementation.

### Observed Failure Modes

The original memory system (`store_memory`/`recall_memory`) treated all persistent knowledge as discrete items in a semantic search collection. This revealed several failure modes:

1. **Retrieval failures** — The agent stored user preferences but semantic search didn't reliably surface them at the right moment
2. **Context fragmentation** — Preferences scattered across many small memories, requiring multiple recalls to build a coherent picture
3. **Lack of self-improvement** — The agent could store facts but not evolve its "mental model"
4. **Session discontinuity** — Each conversation started cold; the agent rediscovered things it should already know

The root insight: **foundational knowledge shouldn't depend on probabilistic retrieval**. Some knowledge should be *constitutive* of the agent's reasoning — always present, shaping how it thinks — rather than discovered mid-conversation through queries.

This mirrors how `CLAUDE.md` works: it's not queried, it's *present*. The agent doesn't ask "what are the project conventions?" — it already knows because they're part of its context.

---

## Alternatives Considered

### Alternative 1: Better Memory Search

**Approach**: Keep the existing memory architecture, improve recall reliability through better embeddings, query strategies, or retrieval prompting.

**Why rejected**: Addresses symptoms, not the root cause. Even perfect semantic search requires the agent to *think to ask*. Foundational context should inform reasoning without explicit retrieval.

### Alternative 2: Memory with Key Taxonomy

**Approach**: Keep `store_memory`/`recall_memory` but add prescribed key conventions (`pref.scheduling.deep_work`, `pattern.tasks.monday_reschedule`) and CRUD operations (`update_memory`, `delete_memory`).

**Why rejected**: Partially addresses key proliferation and CRUD gaps, but doesn't solve the fundamental retrieval problem. Agent still needs to recall at the right moment. Also imposes structure that should emerge from agent reasoning (against ANA philosophy).

### Alternative 3: Always-Injected Memory Dump

**Approach**: Inject all stored memories at session start, regardless of relevance.

**Why rejected**: Doesn't scale. Memory collection grows unbounded; eventually exceeds context limits or drowns signal in noise.

### Alternative 4: Global Context as First-Class Concept (Chosen Direction)

**Approach**: Introduce Global Context as a distinct layer — always present, agent-maintained — independent of how other memory (Items, Entity Context, semantic search) is implemented.

**Why chosen**:
- Solves retrieval problem for foundational knowledge (it's always there)
- Orthogonal to other memory decisions — enhances any architecture
- Clear mental model for the agent
- Aligns with ANA: agent reasons about what belongs where
- Future Entity Context or memory improvements layer cleanly on top

### Alternative 5: Three-Tier with Entity Context

**Approach**: Add a third tier for knowledge about specific entities (people, projects, companies) — important when relevant but shouldn't clutter Global Context.

**Status**: Deferred for future consideration. MVP proceeds with two tiers. See "Deferred: Entity Context" section below.

---

## Architecture (MVP)

| Layer | Purpose | Retrieval | Mutability |
|-------|---------|-----------|------------|
| **Global Context** | Shapes how agent thinks | Always injected | Agent-evolved (line tools) |
| **Items** | Discrete things with lifecycle | RAG (semantic) | CRUD tools |

**GC is additive.** It can coexist with the current memory tools, though in practice much of what was stored via `store_memory` would migrate to GC:
- Foundational knowledge → Global Context (always present)
- Episodic/factual → Items or existing memory (RAG-surfaced when relevant)

Future enhancements (Entity Context, improved memory search) layer cleanly on top of GC — they address different needs.

---

## Global Context Mechanism

### Injection

GC is injected via `{{global_context}}` placeholder in the system prompt, wrapped in `<global-context>` tags. The agent understands: everything above the tags is immutable instructions, everything inside is learned context it can modify.

```markdown
# System Prompt (immutable)
...all guidance...

Today's date: {{today}}

<global-context>
0-- Prefers deep work in mornings
1-- Often reschedules Monday tasks to Tuesday
2-- Acme project is high priority this quarter
</global-context>
```

### Line-Addressable Editing

GC is presented as a line-numbered document. Tools:

- `append_context(content)` — Add new line to end
- `replace_context(line, content)` — Update existing line
- `delete_context(line)` — Remove line

**Why line-addressable?** Simple mental model (like editing a file), precise updates, no complex data structures. Agent sees a document, makes surgical changes.

### Line Stability Model

**During session**:
- `delete_context(line)` replaces content with empty string
- Line indices remain stable (no reindexing mid-session)
- Agent's mental model stays valid

**Between sessions**:
- Backend compacts: `\n{2,}` → `\n`
- Reindexes from 0
- Agent gets clean, compacted document

**Why this approach?** Considered alternatives:
- *Delete with immediate reindex*: Agent's line references invalidate
- *Stable UUIDs per line*: Becomes key-value system again
- *No delete, only replace with empty*: Accumulates cruft

Session-scoped stability with between-session compaction gives the best of both: stable references while editing, no cruft accumulation over time.

### Initial State

Empty Global Context with system prompt guidance explaining the blank slate. No placeholder content, no forced onboarding. Agent populates naturally through interaction.

---

## System Prompt Guidance

```markdown
## Global Context

As you interact with the user, you will become aware of preferences,
patterns, and context that any agent should know when working with them.
This is your **Global Context** — persistent knowledge that shapes how
you assist.

### What belongs in Global Context
- Preferences: "Prefers deep work in mornings", "Likes concise responses"
- Patterns: "Often reschedules Monday tasks", "Reviews email at 9am and 4pm"
- Constraints: "Picks up kids at 3pm weekdays", "No meetings before 10am"
- Domain context: "Acme project is high priority this quarter"
- Your observations: Patterns you notice that the user hasn't explicitly stated

### What does NOT belong
- Specific tasks or events → create an Item
- One-time facts → just respond, don't store
- Things that will change soon → not worth persisting

### Tools
- `append_context(content)` — Add a new line to Global Context
- `replace_context(line, content)` — Update an existing line
- `delete_context(line)` — Remove a line (no longer relevant)

Global Context is currently empty. As you learn about the user, populate it.
```

### No Prescribed Taxonomy

The agent develops its own organization for Global Context. No required prefixes (`pref.`, `pattern.`) or structure. This aligns with ANA philosophy: agent reasons about what structure is appropriate, conventions emerge through use rather than being prescribed.

---

## Deferred: Entity Context

### Premise

Some knowledge is about specific entities (people, projects, companies, domains) — important when relevant but shouldn't clutter Global Context.

**Distinction from Global Context**: GC shapes *how the agent thinks*. Entity Context is *what the agent knows about specific things in the user's world*.

**Distinction from Items**: Items have lifecycle (status, completion). Entity Context is reference knowledge without actionability.

### Example Boundaries

| Input | Where | Why |
|-------|-------|-----|
| "I prefer async communication" | Global Context | User pattern, shapes all interactions |
| "Sarah prefers async communication" | Entity Context | About Sarah, relevant when discussing her |
| "Message Sarah about the proposal" | Item | Actionable task |

### Design Questions (To Resolve)

- Separate collection or item type with `entity` metadata?
- Dedicated tools or just guidance in system prompt?
- How does agent decide: GC vs Entity Context vs Item?
- What's the retrieval mechanism? (Always RAG, or something else?)

### Why Deferred

MVP can function with two tiers. Items with good semantic content can serve as proto-Entity Context — "Sarah prefers async" stored as an item will surface when the agent queries about Sarah.

The question is whether the distinction provides enough value to warrant explicit tooling. Revisit after validating the GC + Items model.

---

## Implementation Status

**Implemented.** The following changes were made:

| File | Changes |
|------|---------|
| `agent_native_app/store.py` | Added `upsert()` method to `Store` protocol and `ChromaStore` |
| `agent_native_app/tools.py` | Added `append_context`/`replace_context`/`delete_context` tools with schemas; dedicated `global_context` collection |
| `agent_native_app/prompts/system.md` | Added Global Context section with `{{global_context}}` placeholder in `<global-context>` tags |
| `agent_native_app/agent.py` | Loads GC at session start, compacts empty lines, injects into prompt |

**Memory tools deprecated.** The `store_memory`/`recall_memory` tools were removed. GC + Items covers the use cases:
- Foundational knowledge → Global Context (always present)
- Episodic/discrete things → Items (semantic search via `query_items`)

---

## Design Principles Honored

- **ANA-aligned**: Agent reasons about what to store, develops own organization
- **Minimal mechanism**: Line-addressable text, not complex data structures
- **Orthogonal**: GC is additive — enhances any memory architecture, doesn't require replacing existing mechanisms
- **Clear boundaries**: GC (constitutive) vs Items (episodic) vs future Entity Context (reference)
- **Session-aware**: Stability during session, cleanup between sessions
- **Semantic-first**: Structure emerges from agent understanding, not prescribed schemas
