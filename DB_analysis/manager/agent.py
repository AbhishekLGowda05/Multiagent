import os
from google.adk.agents import Agent

from manager.sub_agents.sales_agent.agent import sales_agent
from manager.sub_agents.greeting_agent.agent import greeting_agent
from manager.sub_agents.diagnostic_agent.agent import diagnostic_agent
from manager.sub_agents.predictive_agent.agent import predictive_agent
from manager.sub_agents.prescriptive_agent.agent import prescriptive_agent





root_agent = Agent(
    name="manager",
    model="gemini-2.0-flash",
    description="Manager agent",
    instruction="""

    You coordinate a team of specialized agents that analyse data from the
    Tally database.

    Delegate each user request to the most relevant agent:
    - **greeting_agent** – welcomes users and collects their name.
    - **sales_agent** – provides descriptive summaries of sales and invoices.
    - **diagnostic_agent** – explains why revenue changed over time.
    - **predictive_agent** – forecasts future sales trends.
    - **prescriptive_agent** – suggests actions to improve performance or retain customers.

    Always choose the best agent for the question. Respond directly if a simple
    greeting is required.

    """,
    sub_agents=[
        sales_agent,
        greeting_agent,
        diagnostic_agent,
        predictive_agent,
        prescriptive_agent,
    ],


    

)
