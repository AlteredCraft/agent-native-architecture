# Agent Native Architecture: A Design Paradigm for LLM-Centered Applications

## Abstract

We introduce **Agent Native Architecture (ANA)**, a software design paradigm where an AI agent serves as the reasoning core of an application, with data structure emerging at runtime through the agent's understanding rather than being predetermined at design time. ANA represents an evolution beyond AI-enhanced and AI-first approaches, inverting the traditional relationship between schema and understanding: structured data becomes an *output* of reasoning, not an *input* required from users or hardcoded by developers. We define the core requirements for ANA, introduce the concept of *schema hint level* as a key design dimension, and discuss the tradeoffs inherent in this approach. A companion implementation—an agent-native personal assistant—validates these concepts through experimentation.

## 1. Introduction

The integration of large language models (LLMs) into software applications has followed a predictable pattern: take an existing application architecture, identify features that could benefit from language understanding, and add AI capabilities as an enhancement layer. This approach—which we term *AI-enhanced*—treats the LLM as a sophisticated feature rather than a foundational component.

A more recent pattern, *AI-first* design, centers the application around AI capabilities from inception. However, even AI-first applications typically maintain traditional schema-driven architectures. The data model is defined at design time; the AI operates within those structural constraints.

This paper proposes a further evolution: **Agent Native Architecture**, where the LLM agent is not merely central but *generative* of structure itself. The schema emerges from the agent's reasoning at runtime, rather than being predetermined by developers.

We explore this paradigm through a concrete implementation—a personal assistant/todo application—chosen for its familiarity and discrete scope. The contribution is not the application itself but the architectural patterns it reveals.

### 1.1 The Fundamental Inversion

Traditional applications are **schema-first**: developers define data models, build features around them, then optionally add AI. The schema dictates what the application can understand and express.

Agent Native applications are **semantic-first**: the agent's understanding of language and context is the core. Structured data becomes an output of reasoning, not an input required from users.

```
Traditional:    User → [Schema] → Database → AI (optional)
Agent Native:   User → [Agent] → Structure emerges → Storage
```

Consider a task management application. In traditional design, a `Task` model defines required fields: `title`, `due_date`, `project_id`, `priority`. Users must translate their intentions into this structure. In an agent-native design, the user says "remind me to call Mom before my flight tomorrow," and the agent produces appropriate structure—a task linked to a calendar event, with temporal context, without requiring the user to understand or manipulate the underlying schema.

This inversion has cascading implications for interface design, workflow flexibility, and emergent capabilities.

## 2. Defining "Agent"

The term "agent" is overloaded in both AI and software engineering contexts. For the purposes of Agent Native Architecture, we define an agent by three necessary properties:

| Property | Description |
|----------|-------------|
| **Goal-directed reasoning** | Pursues objectives through multi-step planning, not merely responding to prompts |
| **Tool use** | Affects the world through actions, not just generates text |
| **Persistence** | Maintains state across interactions |

These properties distinguish agents from adjacent concepts:

- A **stateless LLM call** (inference) lacks all three properties
- A **chatbot with conversation history** has persistence but typically lacks goal-direction and tool use
- A **workflow/pipeline with LLM steps** may use tools but lacks autonomous reasoning—the orchestration is predetermined

An agent combines goal-directed reasoning with the ability to affect state through tools, while maintaining memory across interactions. For short-running agents, persistence may be achieved through the context window alone; long-running agents require external memory mechanisms.

The term "Agent Native" therefore implies an architecture that supports goal-directed, tool-using, persistent behavior as a foundational capability, not an optional feature.

## 3. Core Requirements

For an architecture to qualify as Agent Native, three requirements must be satisfied:

### 3.1 LLM as Reasoning Core

The agent is the decision-making engine, not a feature layered onto existing logic. User intentions flow through the agent's understanding before being translated into structured operations. This distinguishes ANA from AI-enhanced approaches where the LLM handles specific features (autocomplete, summarization, search) while traditional code handles core logic.

### 3.2 Runtime Schema Emergence

Structure is determined during execution, not fixed at design time. The agent decides what properties are relevant for a given item, what relationships exist between items, and how information should be organized. This does not mean the absence of schema—rather, it means the agent participates in schema definition.

In practice, this manifests through flexible primitives. Rather than `create_task(title, due_date, project_id)`, the agent operates with `create_item(content, properties)` where properties are open-ended. The agent reasons about what structure is appropriate for each interaction.

### 3.3 Memory Mechanism

Agents require persistence across interactions to learn user patterns, maintain context, and improve over time. Within a single session, the LLM's context window may suffice. For agents operating across multiple sessions—where continuity matters but the context window resets—external memory becomes essential.

ANA distinguishes two categories of persistent knowledge:

- **Constitutive knowledge** (Global Context): Foundational understanding that should *always be present*—user preferences, behavioral patterns, constraints, and the agent's evolving model of the problem space. This knowledge shapes how the agent reasons and should not depend on retrieval. Global Context is analogous to the system prompt: both are always-present knowledge that shapes reasoning. The distinction is authorship—the system prompt is developer-controlled (defining agent persona and behavior), while Global Context is agent-controlled (adapting to a specific user over time).
- **Episodic knowledge** (Items): Discrete things with lifecycle—tasks, notes, reminders. Retrieved through semantic search (RAG) when relevant to the current context.

This distinction emerged from implementation experience: treating all persistent knowledge as retrievable items led to failures where foundational preferences weren't surfaced at the right moment. Some knowledge should be *constitutive* of reasoning, not discovered mid-conversation through probabilistic retrieval.

The memory *mechanism* is architectural—ANA requires it. What the agent *stores* and *where* is behavioral—guided by system prompts. Effective implementations should prompt the agent to distinguish between knowledge that shapes all reasoning (Global Context) versus knowledge relevant to specific queries (Items).

## 4. The Schema Hint Spectrum

Agent Native does not mean "no schema." It means the agent participates in schema definition. How much structure developers provide is a design choice—what we term the **schema hint level**.

### 4.1 Hint Surfaces

Schema hints can be applied at multiple architectural layers:

| Layer | High-hint | Low-hint |
|-------|-----------|----------|
| **Tools** | `create_task(title, due_date, project)` | `create_item(content, properties)` |
| **System Prompt** | "Tasks have priorities 1-4; statuses are: active, done, blocked" | "Items can have any properties you find useful" |
| **Examples** | Few-shot examples with rigid structure | Examples demonstrating flexible, emergent structure |

### 4.2 The Design Space

These hint surfaces create a two-dimensional design space:

```
                    Tool Hints
                 Low ←────────→ High
              ┌─────────────────────┐
        Low   │  Maximum emergence  │  Tools constrain,
   Prompt     │  (experimental)     │  prompt is loose
   Hints      ├─────────────────────┤
        High  │  Prompt guides,     │  Traditional
              │  tools are flexible │  (fully specified)
              └─────────────────────┘
```

### 4.3 The Spectrum

Along the tool dimension specifically:

```
Schema Hint Level
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
High-hint           Medium-hint          Low-hint          Zero-hint
create_task()       create_item()        store()           [pure text]
update_task()       update_item()        retrieve()
complete_task()     delete_item()
assign_project()    query_items()
                    append_context()
                    replace_context()
                    delete_context()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Traditional         ← Agent Native →                       Impractical
```

**High-hint** tools encode domain concepts. The schema is mostly predetermined; the agent fills in values within constraints. Here, the agent primarily serves as a *translator*—converting natural language into predefined structure rather than determining what structure should exist.

**Medium-hint** tools provide operation semantics (CRUD) without domain constraints. The agent decides what "item" means and what properties matter.

**Low-hint** tools offer minimal structure. The agent must reason about everything, including whether an operation is a create or update.

### 4.4 Optimal Balance

For most ANA implementations, the optimal position is **low-hint tools combined with medium-hint system prompts**. This provides:

- **Determinism at the operation level**: You know a `create_item` occurred; operations are auditable
- **Flexibility at the domain level**: The agent decides what properties matter for each item
- **Guidance without constraint**: The system prompt teaches conventions and patterns without enforcing rigid rules

This balance acknowledges a practical reality: even with minimal tool hints, the agent will develop implicit conventions. Providing operation-level structure (CRUD) captures well-understood semantics without constraining domain modeling.

## 5. Capabilities Enabled

Agent Native Architecture changes not just how applications are built but what becomes possible.

### 5.1 Runtime Schema Emergence

The agent determines appropriate structure for each item based on context. A task might acquire `priority`, `due_date`, and `project` properties. A quick note might have only `context`. The same primitive serves both—structure emerges from understanding rather than rigid field requirements.

### 5.2 Cross-Domain Reasoning

Traditional applications are silos; information in one system doesn't inform another. An agent can connect information that users would never manually link: flight times, task deadlines, contact timezone differences, and user preferences can all inform a single recommendation. This requires structure—but structure the agent can reason across, not structure that isolates domains.

### 5.3 Emergent Features

Capabilities need not be predetermined. "Show me everything related to the Q3 launch" requires no special feature—the agent queries semantically. "What patterns do you see in my completed tasks?" requires no analytics dashboard—the agent reasons over available data. Features emerge from understanding combined with tools, not from predetermined code paths.

### 5.4 Learning Without Retraining

As users provide feedback, the agent adapts through memory. "I prefer deep work in the morning" is stored and influences future recommendations. Behavior changes within interactions, not deployment cycles. This is fundamentally different from traditional ML systems requiring retraining—adaptation is immediate through in-context learning and memory retrieval.

### 5.5 Proactive Behavior

Because the agent manages structure and maintains memory, it can notice patterns and initiate action: "You've rescheduled this task three times. Want to break it down or delegate it?"

This capability emerges directly from ANA's core properties. The agent controls how information is structured, so it can organize data in ways that surface patterns. It maintains memory across sessions, so it can detect trends over time. And it reasons over both, identifying opportunities for intervention that a reactive system—waiting for explicit commands—would never surface.

Not all ANA applications require proactivity, but the architecture enables it. The agent has sufficient context (memory), capability (tools), and understanding (structure it created) to move beyond purely reactive behavior.

### 5.6 Future Direction: Adaptive Interfaces

The ANA pattern extends naturally to user interfaces. Provide the agent with UI primitives and interfaces can reshape based on user intent. "Show me tasks grouped by energy level, not project" becomes achievable without developer intervention. This represents a significant extension of the paradigm warranting separate exploration.

## 6. Boundaries and Tradeoffs

### 6.1 What ANA Is Not

**Not "chatbot replaces UI."** Structured interfaces retain value for glanceable information, quick actions, and spatial navigation. The shift is in control: the agent becomes primary for complex or ambiguous tasks; structured UI handles rapid, well-defined interactions.

**Not schema-less.** The agent produces structure; it does not avoid it. Items have properties; memories are retrievable by semantic relevance; operations have results. The difference is *who defines* that structure and *when*—the agent at runtime rather than developers at design time.

**Not non-deterministic chaos.** Schema hints at tool and prompt layers provide a foundation of determinism. Operations are auditable; tool calls are traceable. The agent's reasoning is flexible, but the operations it produces are concrete and logged.

**Not universally applicable.** ANA suits domains characterized by ambiguity, personalization, and evolving requirements—personal assistants, knowledge work tools, creative applications. Systems requiring deterministic guarantees (financial ledgers, safety-critical systems) need architectural properties ANA does not provide.

### 6.2 The Core Tradeoff

ANA trades deterministic predictability for adaptive capability. In traditional architectures, behavior is fully specified: given input X, the system produces output Y. In ANA, behavior emerges from reasoning: given input X, the agent determines appropriate action based on context, memory, and understanding.

This is an early-stage architectural experiment. Rather than prescribing "use ANA here, not there," we aim to articulate the tradeoffs clearly so practitioners can make informed decisions. That said, current model capabilities allow us to identify where ANA appears more or less appropriate.

ANA tends to fit well when:
- User needs vary significantly and unpredictably
- Domain concepts are fuzzy or evolving
- Personalization provides substantial value
- Exact reproducibility is less important than contextual appropriateness

The tradeoff is inappropriate when:
- Regulatory requirements demand deterministic behavior
- Errors have severe, irreversible consequences
- Audit trails require exact reproducibility
- Users need guaranteed response times

### 6.3 Trust and Transparency

Non-deterministic systems require different trust mechanisms than deterministic ones. Users cannot rely on "I clicked this button, so that happened." Instead, trust builds through:

- **Explainability**: The agent articulates its reasoning
- **Recoverability**: Misinterpretations can be corrected after the fact; the system doesn't demand perfect understanding upfront
- **Graduated autonomy**: The agent earns expanded authority through demonstrated competence
- **Transparency**: Users can inspect what the agent did and why

These mechanisms do not eliminate the trust challenge but provide a framework for navigating it.

## 7. Implementation Notes

The companion repository implements these concepts through a personal assistant application with the following characteristics:

**Seven primitive tools** at the medium-hint level:
- `create_item`, `update_item`, `delete_item`, `query_items` (CRUD for flexible items)
- `append_context`, `replace_context`, `delete_context` (Global Context management)

**System prompt** providing domain guidance without rigid rules—teaching the agent how to think about tasks, priorities, and context without enforcing specific schemas.

**Single persistence layer** (ChromaDB) enabling semantic search across all stored information. This is an implementation choice, not an architectural requirement—the system abstracts storage behind a protocol allowing alternative implementations.

One implementation detail worth noting: ChromaDB's semantic search operates on document content, not metadata. Properties stored as metadata (e.g., `due_date: "2026-01-13"`) are invisible to queries like "what's due Tuesday?" The implementation addresses this by embedding properties into document content with dates converted to human-readable format, then stripping them on retrieval. This is a workaround for a specific persistence layer limitation, not an architectural pattern.

**Conversation-based interface** demonstrating the primary interaction pattern, with structured UI as a future extension.

The implementation validates the core hypothesis: meaningful task management emerges from minimal primitives combined with LLM reasoning, without requiring traditional schema-first design.

## 8. Design Evolution

ANA is explicitly an architectural experiment. The patterns described in this paper emerged through iterative implementation, not upfront specification. Documenting one such evolution illustrates how ANA projects should expect to adapt.

The original implementation included `store_memory` and `recall_memory` tools—a semantic search layer for all persistent knowledge. During testing, this revealed a failure mode: foundational preferences weren't reliably surfaced at the right moment. The agent stored "prefers deep work in mornings" but semantic search didn't consistently retrieve it when planning a user's day.

The root insight: **some knowledge should be constitutive of reasoning, not dependent on retrieval**. This led to Global Context—always-present knowledge injected into every interaction, analogous to how a system prompt shapes behavior without being queried.

This isn't a failure of the original design but a validation of ANA's core premise: when the agent participates in schema definition, the architecture can evolve based on observed behavior rather than speculative requirements. The abstract `Store` protocol allowed swapping memory implementations without touching tool or agent code.

For detailed design rationale including alternatives considered, see the companion [Global Context Design](global-context.md) document.

## 9. Conclusion

Agent Native Architecture represents a meaningful evolution in how LLM-powered applications can be designed. By positioning the agent as the reasoning core and allowing structure to emerge at runtime, ANA enables capabilities difficult or impossible to achieve in schema-first architectures: cross-domain reasoning, emergent features, immediate personalization, and proactive behavior.

A practical advantage deserves emphasis: ANA systems are significantly easier to tune toward desired behavior. Adjusting a system prompt or modifying tool hints is far more accessible than refactoring tightly-coupled schemas. This makes iteration faster and lowers the barrier for non-engineers to shape system behavior.

The approach is not universally applicable. It trades deterministic predictability for adaptive capability—a tradeoff appropriate for domains characterized by ambiguity and personalization, inappropriate for domains requiring guaranteed behavior.

The key conceptual contributions are:
1. **The fundamental inversion**: Structure as output, not input
2. **Schema hint level** as a design dimension with multiple surfaces (tools, system prompts, examples)
3. **Clear criteria** distinguishing ANA from AI-enhanced and AI-first approaches

We offer this framework not as a complete theory but as a working vocabulary for practitioners building LLM-centered applications. The paradigm is nascent; we expect the patterns to evolve as the community accumulates implementation experience.

---

## References

*To be added.*
