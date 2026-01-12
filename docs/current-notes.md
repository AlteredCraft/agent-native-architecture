# Notes

This is an ephemeral list of considerations i'd like to review later.

- [ ] DO NEXT : review the management of memory.
    - Should we encourage the agent to persist learned 'schemas' in memory? For example, if the user frequently adds tasks with a 'project' property, should the agent remember this preference and suggest it in future interactions?
    - Should we have Update (and Delete) for memories?  What is the minimal directive for memory management in an ANA context?
    - Make any needed changes to the system prompt to reflect the desired memory management strategy. (in addition to code changes) 

- [ ] Context is the critical resource for agents. We might consider leveraging sub-agents to handle common tasks, only returning the result to the main agent. This would help manage context window limitations.

- [ ] In this post, Link to previous post , this also spoke to less code, more llm agency
  - URL: https://alteredcraft.com/p/zero-lines-of-python
  - cotent: `/Users/sam/_PRIMARY_VAULT/AlteredCraft/Altered Craft Publications/LongFormWriting/Posts in process or complete/Progress towards dev journal/post content.md`
