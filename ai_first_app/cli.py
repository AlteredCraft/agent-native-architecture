"""
Command-line interface for the AI-First Todo assistant.
"""

from .agent import Agent
from .config import Config


def main(config: Config):
    """Run the interactive CLI."""
    print("AI-First Todo Assistant")
    print("=" * 40)
    print("Type your message and press Enter.")
    print("Commands: /quit, /reset, /help")
    print()

    agent = Agent(config)

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.lower() == "/quit":
            print("Goodbye!")
            break
        elif user_input.lower() == "/reset":
            agent.reset()
            print("Conversation reset.")
            continue
        elif user_input.lower() == "/help":
            print("""
Commands:
  /quit   - Exit the assistant
  /reset  - Clear conversation history
  /help   - Show this help message

Just type naturally to interact with your assistant.
Examples:
  - "Add a task to review the quarterly report"
  - "What do I have to do today?"
  - "Mark the grocery task as done"
  - "I prefer to work on hard tasks in the morning"
""")
            continue

        # Get response from agent
        try:
            response = agent.chat(user_input)
            print(f"\nAssistant: {response}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
