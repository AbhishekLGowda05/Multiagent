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

    You are responsible for delegating tasks to the following agent:
    - sales_agent
    -greeting_agent
    -diagnostic_agent
    -predictive_agent

    You also have access to the following sub- agents:
    - sales_agent
    -greeting_agent
    -diagnostic_agent
    -predictive_agent

    in case the relevant agent is not found delegate back to the root agent and check for the subagents available for tasks again
    """,
    sub_agents=[sales_agent,greeting_agent,diagnostic_agent,predictive_agent],
    
)
