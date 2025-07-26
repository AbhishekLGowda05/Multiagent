from agents.base import BaseAgent

financial_agent = BaseAgent(
    name="financial_agent",
    model="gemini-2.0-flash",
    description="Handles financial queries.",
    tools=[],
    instruction="Forward financial questions to the correct analytics tool.",
)
