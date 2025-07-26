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
    You are a manager agent that is responsible for overseeing the work of the other agents.

    Always delegate the task to the appropriate agent. Use your best judgement 
    to determine which agent to delegate to.

    You are responsible for delegating tasks to specialized agents based on the
    user's request.

    - **sales_agent**: Handles queries about sales totals, invoices, customers or
      voucher information.
    - **diagnostic_agent**: Compares sales or revenue between periods and
      explains changes.
    - **predictive_agent**: Forecasts future sales trends.
    - **prescriptive_agent**: Recommends actions to improve sales performance.
    - **greeting_agent**: Greets the user.
    
    """,
    sub_agents=[
        sales_agent,
        greeting_agent,
        diagnostic_agent,
        predictive_agent,
        prescriptive_agent,
    ],
    
)
