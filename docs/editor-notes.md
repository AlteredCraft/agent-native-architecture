# Editor Notes: Agent Native Architecture Definition

These notes capture the reasoning behind `article.md`—the decisions made, alternatives considered, and rationale for key framings. Use this when adapting other docs or extending the article.

---

## Origin

The goal was to produce a crisp, complete definition of "Agent Native Architecture" (ANA) that could:
1. Anchor the architecture of the companion todo app
2. Serve as the basis for a research article (arXiv-style)
3. Be accessible to developers while also reaching product/design thinkers

---

## Key Framing Decisions

### The Evolutionary Position

We positioned ANA as an evolution, not a revolution:

```
AI-enhanced → AI-first → Agent Native
```

- **AI-enhanced**: Traditional app with AI bolted on (autocomplete, suggestions)
- **AI-first**: App designed around AI, but still schema-predefined at design time
- **Agent Native**: Agent participates in schema definition at runtime

This framing is intentionally non-combative with existing "AI-first" usage in the community. Many will use the terms interchangeably—we're carving out a specific meaning for ANA without invalidating adjacent terminology.

### The Fundamental Inversion

The core differentiator: **structured data as output, not input**.

In traditional apps, users must translate intentions into schema-compliant input. In ANA, users express intent naturally; structure emerges from the agent's understanding.

This is the one-liner that should stick: *"Structure as output, not input."*

### Why "Semantic-First" vs "Schema-First"

We use "semantic-first" to describe ANA's orientation. The term emphasizes that the LLM's understanding of meaning is the foundation—schema becomes a byproduct of that understanding, not a prerequisite for it.

---

## The Agent Definition

We defined "Agent" by three necessary properties:

| Property | Why It Matters |
|----------|----------------|
| **Goal-directed reasoning** | Distinguishes from chatbots (which respond) and pipelines (which execute predefined flows) |
| **Tool use** | Distinguishes from pure inference—agents affect state, not just generate text |
| **Persistence** | Distinguishes from stateless calls—continuity enables learning and context |

This definition matters because it's in the name: "Agent Native." We needed clarity on what "Agent" means in this context.

### Memory: Multi-Session, Not "Long-Running"

Early drafts said "long-running agents need external memory." This was imprecise. The real distinction:

- **Within a session**: Context window may suffice
- **Across sessions**: External memory is essential (context resets)

"Long-running" conflated duration with session boundaries. Multi-session is the clearer framing.

---

## The Schema Hint Spectrum

This emerged as a key contribution—a design dimension we hadn't seen articulated elsewhere.

### The Insight

ANA doesn't mean "no schema." It means the agent participates in schema definition. *How much* structure you provide is a design choice—the "schema hint level."

### Two Hint Surfaces

Schema hints apply at multiple layers:

1. **Tools**: `create_task(title, due_date)` vs `create_item(content, properties)`
2. **System Prompt**: "Tasks have priorities 1-4" vs "Items can have any properties"
3. **Examples**: Rigid few-shot examples vs flexible demonstrations

This creates a 2D design space (tool hints × prompt hints), not a single spectrum.

### The Spectrum Table

```
High-hint → Medium-hint → Low-hint → Zero-hint
create_task()  create_item()  store()   [pure text]
```

We placed ANA in the medium-hint zone. The companion app uses:
- Low-hint tools (generic CRUD)
- Medium-hint prompts (domain guidance without rigid rules)

### High-Hint = Translator

Key insight from review: at the high-hint end, the agent primarily serves as a *translator*—converting natural language to predefined structure. It's not determining what structure should exist; it's filling in predetermined fields.

This clarifies why high-hint isn't really "Agent Native"—the agent isn't participating in schema definition, just schema population.

### "Sweet Spot" → "Optimal Balance"

Changed terminology for professional/academic tone. Same concept: low-hint tools + medium-hint prompts.

---

## Capabilities Section

### What We Included

- **Runtime schema emergence**: The defining capability
- **Cross-domain reasoning**: Agent connects information across silos
- **Emergent features**: Capabilities without predetermined code paths
- **Learning without retraining**: Immediate adaptation through memory
- **Proactive behavior**: Agent initiates, not just responds

### What We Excluded (for now)

**Adaptive interfaces**: We flagged this as a "future direction" rather than a core capability. The reasoning:

1. The companion app doesn't implement adaptive UI
2. It's the same pattern (UI primitives instead of schema primitives) but deserves its own exploration
3. Including it as a core capability would oversell what the current implementation demonstrates

### Proactive Behavior: Why It Emerges from ANA

Expanded this section during review. The key insight:

> The agent controls how information is structured, so it can organize data in ways that surface patterns. It maintains memory across sessions, so it can detect trends over time. And it reasons over both, identifying opportunities for intervention.

Proactivity isn't a separate feature—it emerges from ANA's core properties (structure control + memory + reasoning).

---

## Boundaries Section

### "What ANA Is Not"

These clarifications prevent misunderstanding:

- **Not "chatbot replaces UI"**: Structured UI retains value
- **Not schema-less**: Structure exists; who defines it and when changes
- **Not non-deterministic chaos**: Operations are auditable
- **Not universally applicable**: Doesn't fit all domains

### The Core Tradeoff

ANA trades deterministic predictability for adaptive capability.

**Reframing from review**: We softened the prescriptive tone. Early draft read like "use ANA for X, not Y." Revised to:

> This is an early-stage architectural experiment. Rather than prescribing "use ANA here, not there," we aim to articulate the tradeoffs clearly so practitioners can make informed decisions.

This is honest—we're exploring, not prescribing.

### Reversibility → Recoverability

Changed terminology. "Reversibility" implies undo. "Recoverability" better captures the real property: misinterpretations can be corrected after the fact. The system doesn't demand perfect understanding upfront.

---

## Trust and Transparency

Four mechanisms for building trust in non-deterministic systems:

1. **Explainability**: Agent articulates reasoning
2. **Recoverability**: Corrections possible after misinterpretation
3. **Graduated autonomy**: Agent earns authority over time
4. **Transparency**: Users can inspect what happened and why

These don't eliminate the trust challenge—they provide a framework for navigating it.

---

## Memory: Mechanism vs Behavior

From review, we clarified that memory serves multiple purposes:

1. **User patterns and preferences**: "I prefer deep work in the morning"
2. **Agent's evolving understanding**: The agent's model of the problem space—concepts, relationships, conventions

Both persist across sessions. The second is easy to overlook but important—the agent doesn't just remember what the user said; it remembers what it has learned about the domain.

### The Key Distinction

We added language to the article clarifying:

- The memory **mechanism** is architectural (ANA requires it)
- **What gets stored** is behavioral (guided by system prompt)

This matters because you could argue "just prompt the agent to store its understanding"—and that's true! But if you don't, and the agent rediscovers structure every session, you lose the continuity that makes ANA different from stateless AI-enhanced systems.

So: memory tools are required, prompting the agent to use them for domain understanding is strongly encouraged but not strictly architectural.

---

## Conclusion: Easier Tuning

Added from review:

> ANA systems are significantly easier to tune toward desired behavior. Adjusting a system prompt or modifying tool hints is far more accessible than refactoring tightly-coupled schemas.

This is a practical advantage that deserves emphasis. Iteration speed matters, and ANA lowers the barrier for non-engineers to shape system behavior.

---

## Audience Notes

**Primary**: Developers building LLM-powered applications
**Secondary**: Product/design thinkers

**Approach**: Layered writing
- Accessible concepts that work for both audiences
- Deep technical details live in repo README, not the article
- arXiv-style structure for future formal publication

---

## What's Next

- [x] Adapt README.md to align with article.md terminology (done: terminology aligned, links added)
- [x] Update implementation-plan.md with schema hint framing (done: added §Schema Hint Level, expanded Memory section with CRUD/key design)
- [x] Consider blog-post-the-app-is-dead.md alignment — keeping as philosophy piece, added cross-link to article.md
- [ ] Experiment: 2-tool version (store/retrieve) to test low-hint extreme
- [ ] Find high-quality citations for article.md (current placeholder: "To be added")

---

## Open Questions

1. **Is "Agent Native Architecture" the right term?** We committed to it, but alternatives exist (semantic-first architecture, emergent-schema architecture). ANA emphasizes the agent; alternatives emphasize the mechanism.

2. **Where does the spectrum become "not ANA"?** We said high-hint is "traditional" and the agent is just a translator. Is there a bright line, or is it a gradient?

3. **How do guardrails fit?** We mentioned trust/transparency but didn't deeply explore guardrails. Worth expanding in future work.

4. **Multi-agent scenarios?** The current framing assumes a single agent. How does ANA extend to multi-agent architectures?

5. **Memory CRUD semantics?** Explored in implementation-plan.md §Memory. Update seems necessary; Delete is debatable (append-only with decay might be safer). Not architectural, but important for production systems.
