"""Example integration of Gmail and Calendar tools with a manager agent."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool

from .gmail_tools import send_email
from .calendar_tools import create_event


# Wrapper functions exposed as tools

def send_email_tool(query: str) -> Any:
    """Parse a simple email command and send the message."""
    # Example query: "Send an email to Rahul about the finance meeting at 10 AM."
    match = re.search(r"email to (\w+) .* about (.+)", query, re.I)
    if not match:
        raise ValueError("Could not parse email command")
    to_name, subject = match.groups()
    to_email = f"{to_name.lower()}@example.com"
    body = subject
    return send_email(to_email, subject, body)


def create_event_tool(query: str) -> Any:
    """Parse a simple scheduling command and create a calendar event."""
    # Example query: "Schedule a project review meeting tomorrow from 3 PM to 4 PM."
    # Example patterns:
    #   "Schedule a meeting tomorrow at 11 AM"
    #   "Schedule project review today at 2:30 pm"
    match = re.search(
        r"(today|tomorrow) at (\d+)(?::(\d+))?\s*(am|pm)", query, re.I
    )
    if not match:
        raise ValueError("Could not parse calendar command")

    day, hour, minute, period = match.groups()

    start_date = datetime.utcnow()
    if day.lower() == "tomorrow":
        start_date += timedelta(days=1)

    hour = int(hour)
    if period.lower() == "pm" and hour != 12:
        hour += 12
    elif period.lower() == "am" and hour == 12:
        hour = 0

    minute = int(minute or 0)
    start_time = start_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    summary = re.sub(r"schedule |meeting|today|tomorrow.*", "", query, flags=re.I).strip()
    return create_event(
        summary or "New Event",
        start_time,
        end_time,
    )


# Example manager agent using these tools
manager_agent = Agent(
    name="manager",
    model="gemini-2.0-flash",
    description="Manager agent with Gmail and Calendar tools",
    instruction="You can send emails and create calendar events using the provided tools.",
    tools=[
        FunctionTool(send_email_tool, name="send_email_tool"),
        FunctionTool(create_event_tool, name="create_event_tool"),
    ],
)


if __name__ == "__main__":
    print("Sending sample email...")
    send_email_tool("Send an email to Rahul about the finance meeting at 10 AM.")
    print("Creating sample event...")
    create_event_tool(
        "Schedule a project review meeting tomorrow from 3 PM to 4 PM."
    )
