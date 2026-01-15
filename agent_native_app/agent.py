"""
LLM Agent with OpenRouter integration.

Handles conversation, tool calling, and response generation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

from .config import Config
from .tools import (
    TOOLS, TOOL_SCHEMAS,
    _gc_store, GC_ITEM_ID, _compact_gc, _format_gc_for_display
)

logger = logging.getLogger(__name__)


def load_system_prompt() -> str:
    """Load system prompt from file and inject date/time and Global Context."""
    prompt_path = Path(__file__).parent / "prompts" / "system.md"
    if not prompt_path.exists():
        return "You are a helpful AI assistant for managing tasks and notes."

    prompt = prompt_path.read_text()

    # Inject date/time
    today = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    prompt = prompt.replace("{{today}}", today)

    # Load and compact Global Context (removes empty lines from previous session)
    item = _gc_store.get(GC_ITEM_ID)
    if item:
        compacted = _compact_gc(item.content)
        if compacted != item.content:
            _gc_store.upsert(GC_ITEM_ID, compacted, {"item_type": "global_context"})
        lines = compacted.split("\n") if compacted else []
    else:
        lines = []

    # Format and inject Global Context
    gc_display = _format_gc_for_display(lines)
    prompt = prompt.replace("{{global_context}}", gc_display)

    return prompt


class Agent:
    """AI agent that uses tools to help manage tasks and notes."""

    def __init__(
        self,
        config: Config,
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        """
        Initialize the agent.

        Args:
            config: Application configuration with API key and model
            base_url: API base URL (defaults to OpenRouter)
        """
        self._client = OpenAI(
            api_key=config.openrouter_api_key,
            base_url=base_url
        )
        self._model = config.openrouter_model
        self._system_prompt = load_system_prompt()
        self._messages: list[dict] = []

    def _build_messages(self) -> list[dict]:
        """Build full message list with system prompt."""
        return [
            {"role": "system", "content": self._system_prompt},
            *self._messages
        ]

    def _execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool and return the result."""
        if name not in TOOLS:
            return {"error": f"Unknown tool: {name}"}

        try:
            result = TOOLS[name](**arguments)
            return result
        except Exception as e:
            return {"error": str(e)}

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the assistant's response.

        Handles tool calls automatically in a loop until the assistant
        provides a final text response.

        Args:
            user_message: The user's input

        Returns:
            The assistant's text response
        """
        # Add user message to history
        self._messages.append({"role": "user", "content": user_message})

        while True:
            # Call the LLM
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._build_messages(),
                tools=TOOL_SCHEMAS,
                tool_choice="auto"
            )

            message = response.choices[0].message
            logger.debug(f"💬 LLM response: tool_calls={bool(message.tool_calls)}")

            # Check if we're done (no tool calls)
            if not message.tool_calls:
                # Add assistant response to history
                self._messages.append({
                    "role": "assistant",
                    "content": message.content
                })
                return message.content or ""

            # Process tool calls
            # Add assistant message with tool calls to history
            self._messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Execute each tool call and add results
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                result = self._execute_tool(name, arguments)

                # Add tool result to history
                self._messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

    def reset(self) -> None:
        """Clear conversation history."""
        self._messages = []
