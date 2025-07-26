from agents.base import BaseAgent

inventory_agent = BaseAgent(
    name="inventory_agent",
    model="gemini-2.0-flash",
    description="Handles inventory related queries.",
    tools=[],
    instruction="Forward inventory questions to the correct analytics tool.",
)
