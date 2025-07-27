from google.adk.agents import Agent

financial_agent = Agent(
    name="financial_agent",
    model="gemini-2.0-flash",
    description="Handles financial queries.",
    instruction="Use this agent for financial analysis questions."
)
