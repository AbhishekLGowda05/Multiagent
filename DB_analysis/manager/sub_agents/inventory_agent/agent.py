from google.adk.agents import Agent

inventory_agent = Agent(
    name="inventory_agent",
    model="gemini-2.0-flash",
    description="Handles inventory related queries.",
    instruction="Use this agent for questions about inventory levels and stock."
)
