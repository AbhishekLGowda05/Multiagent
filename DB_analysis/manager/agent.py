import os
from google.adk.agents import Agent

from manager.sub_agents.greeting_agent.agent import greeting_agent
from manager.sub_agents.sales_agent.agent import sales_agent
from manager.sub_agents.purchase_agent.agent import purchase_agent
from manager.sub_agents.inventory_agent.agent import inventory_agent
from manager.sub_agents.financial_agent.agent import financial_agent

root_agent = Agent(
    name="manager",
    model="gemini-2.0-flash",
    description="Orchestrates domain agents for analytics",
    instruction="""
    You are an orchestrator. Determine which business domain
    (sales, purchase, inventory or financial) the user is asking about and
    which analysis type they need (descriptive, diagnostic, predictive or
    prescriptive). Delegate the request to the appropriate domain agent.
    The greeting agent handles salutations and small talk.
    """,
    sub_agents=[
        greeting_agent,
        sales_agent,
        purchase_agent,
        inventory_agent,
        financial_agent,
    ],
)
