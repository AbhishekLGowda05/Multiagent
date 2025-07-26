from agents.base import BaseAgent

purchase_agent = BaseAgent(
    name="purchase_agent",
    model="gemini-2.0-flash",
    description="Handles purchase related queries.",
    tools=[],
    instruction="Forward purchase questions to the correct analytics tool.",
)
