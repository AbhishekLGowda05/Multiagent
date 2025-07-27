from google.adk.agents import Agent

purchase_agent = Agent(
    name="purchase_agent",
    model="gemini-2.0-flash",
    description="Handles purchase related queries.",
    instruction="Use this agent for questions about purchases and vendors."
)
