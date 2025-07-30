import os
import sys
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from manager.cross_agent_orchestrator import CrossAgentOrchestrator, DEFAULT_SPECS

from manager.sub_agents.sales_agent.agent import sales_agent
from manager.sub_agents.greeting_agent.agent import greeting_agent
from manager.sub_agents.purchase_agent.agent import purchase_agent
from manager.sub_agents.inventory_agent.agent import inventory_agent
from manager.sub_agents.financial_agent.agent import financial_agent

# Add the parent directory to sys.path to access google_utils
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import Google utilities
from google_utils.gmail_tools import send_email
from google_utils.calendar_tools import create_event

import re
from datetime import datetime, timedelta
from typing import Any

# Rest of your code remains the same...
cross_orchestrator = CrossAgentOrchestrator(DEFAULT_SPECS)

# Enhanced Google integration tools with better pattern matching
def smart_send_email(query: str) -> Any:
    """Enhanced email tool that can handle business analytics context."""
    # Pattern 1: "Send [content] to [email]"
    pattern1 = re.search(r"send (.+?) to ([\w.+-]+@[\w.-]+\.\w+)", query, re.I)
    # Pattern 2: "Email [name] about [subject]"
    pattern2 = re.search(r"email (\w+) (?:about |the )?(.+)", query, re.I)
    # Pattern 3: "Send email to [name/email] about [subject]"
    pattern3 = re.search(r"send (?:an )?email to ([\w.+-]+@[\w.-]+\.\w+|[\w\s]+) about (.+)", query, re.I)
    # Pattern 4: Direct email format detection
    pattern4 = re.search(r"([\w.+-]+@[\w.-]+\.\w+)", query, re.I)
    
    if pattern1:
        content, to_email = pattern1.groups()
        subject = f"{content.title()}"
        body = f"Hi,\n\nPlease find the {content} as requested.\n\nBest regards"
        return send_email(to_email, subject, body)
    
    elif pattern3:
        to_recipient, subject = pattern3.groups()
        # Check if it's an email address or name
        if "@" in to_recipient:
            to_email = to_recipient
        else:
            to_email = f"{to_recipient.lower().replace(' ', '')}@example.com"
        body = f"Hi,\n\nRegarding: {subject}\n\nPlease find the requested information attached.\n\nBest regards"
        return send_email(to_email, subject, body)
    
    elif pattern4:
        # Found email address in query
        to_email = pattern4.group(1)
        if "profit" in query.lower():
            subject = "Profit Analysis Report"
            body = "Hi,\n\nPlease find the profit analysis report as requested.\n\nBest regards"
        else:
            subject = "Business Report"
            body = "Hi,\n\nPlease find the requested business analysis.\n\nBest regards"
        return send_email(to_email, subject, body)
    
    elif pattern2:
        to_name, subject = pattern2.groups()
        to_email = f"{to_name.lower()}@example.com"
        body = f"Hi {to_name},\n\nRegarding: {subject}\n\nPlease find the requested information.\n\nBest regards"
        return send_email(to_email, subject, body)
    
    else:
        raise ValueError("Could not parse email command. Please provide recipient email or name.")

def smart_schedule_event(query: str) -> Any:
    """Enhanced calendar tool for business meetings and analytics sessions."""
    # Pattern 1: "Schedule [meeting] for [day] at [time]" or "schedule a meeting tomorrow at 11 AM titled 'Title'"
    pattern1 = re.search(r"schedule (?:a )?(?:meeting )?(.+?) (?:for |on )?(today|tomorrow|monday|tuesday|wednesday|thursday|friday) at (\d+)(?::(\d+))?\s*(am|pm)(?:\s*titled\s*['\"](.+?)['\"])?", query, re.I)
    # Pattern 2: "Create meeting [subject] tomorrow from [time] to [time]"
    pattern2 = re.search(r"create (?:meeting |event )?(.+?) (today|tomorrow) from (\d+)\s*(am|pm) to (\d+)\s*(am|pm)", query, re.I)
    # Pattern 3: Enhanced pattern for "schedule meeting tomorrow at 11 AM titled 'Title'"
    pattern3 = re.search(r"schedule (?:a )?meeting (today|tomorrow) at (\d+)(?::(\d+))?\s*(am|pm) titled ['\"](.+?)['\"]", query, re.I)
    # Pattern 4: "Book [meeting type] session [when]"
    pattern4 = re.search(r"book (.+?) session (today|tomorrow)", query, re.I)
    
    base_date = datetime.now()
    
    if pattern3:
        day, start_hour, start_min, start_period, title = pattern3.groups()
        meeting_type = title
        
        # Calculate date
        if day.lower() == "tomorrow":
            base_date += timedelta(days=1)
        
        # Parse start time
        start_hour = int(start_hour)
        if start_period.lower() == "pm" and start_hour != 12:
            start_hour += 12
        elif start_period.lower() == "am" and start_hour == 12:
            start_hour = 0
        
        start_time = base_date.replace(hour=start_hour, minute=int(start_min or 0), second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)  # Default 1 hour meeting
        
        return create_event(meeting_type, start_time.isoformat() + "Z", end_time.isoformat() + "Z")
    
    elif pattern1:
        meeting_type, day, start_hour, start_min, start_period, title = pattern1.groups()
        
        # Use title if provided, otherwise use meeting_type
        if title:
            meeting_type = title
        
        # Calculate date
        if day and day.lower() == "tomorrow":
            base_date += timedelta(days=1)
        elif day and day.lower() == "today":
            pass  # Use current date
        
        # Parse start time
        start_hour = int(start_hour)
        if start_period.lower() == "pm" and start_hour != 12:
            start_hour += 12
        elif start_period.lower() == "am" and start_hour == 12:
            start_hour = 0
        
        start_time = base_date.replace(hour=start_hour, minute=int(start_min or 0), second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        return create_event(meeting_type.title(), start_time.isoformat() + "Z", end_time.isoformat() + "Z")
    
    elif pattern2:
        meeting_type, day, start_hour, start_period, end_hour, end_period = pattern2.groups()
        
        if day.lower() == "tomorrow":
            base_date += timedelta(days=1)
        
        # Parse times
        start_hour = int(start_hour)
        if start_period.lower() == "pm" and start_hour != 12:
            start_hour += 12
        
        end_hour = int(end_hour)
        if end_period.lower() == "pm" and end_hour != 12:
            end_hour += 12
        
        start_time = base_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = base_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        
        return create_event(meeting_type.title(), start_time.isoformat() + "Z", end_time.isoformat() + "Z")
    
    elif pattern4:
        session_type, day = pattern4.groups()
        
        if day.lower() == "tomorrow":
            base_date += timedelta(days=1)
        
        # Default to 2 PM - 3 PM for sessions
        start_time = base_date.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        return create_event(f"{session_type.title()} Session", start_time.isoformat() + "Z", end_time.isoformat() + "Z")
    
    else:
        raise ValueError("Could not parse calendar command. Please specify day and time.")

def combined_analytics_and_email_calendar(query: str) -> Any:
    """Handle queries that combine analytics with email and/or calendar actions."""
    results = {}
    
    # Check if query contains both email and calendar actions
    has_email = any(keyword in query.lower() for keyword in ["send", "email", "@"])
    has_calendar = any(keyword in query.lower() for keyword in ["schedule", "meeting", "calendar"])
    has_analysis = any(keyword in query.lower() for keyword in ["profit", "analysis", "report", "sales", "financial"])
    
    if has_analysis and (has_email or has_calendar):
        # First perform analysis if requested
        if has_analysis:
            analysis_result = cross_orchestrator.handle_query(query)
            results["analysis_result"] = analysis_result
        
        # Then handle email
        if has_email:
            try:
                email_result = smart_send_email(query)
                results["email_result"] = email_result
            except Exception as e:
                results["email_error"] = str(e)
        
        # Then handle calendar
        if has_calendar:
            try:
                calendar_result = smart_schedule_event(query)
                results["calendar_result"] = calendar_result
            except Exception as e:
                results["calendar_error"] = str(e)
        
        results["message"] = "Combined workflow completed successfully"
        return results
    
    raise ValueError("Could not parse combined workflow command")

root_agent = Agent(
    name="manager",
    model="gemini-2.0-flash",
    description="Central orchestrator for analytics requests with Google integration",
    instruction="""
    You are an intelligent Manager Orchestrator with Google Workspace integration (Gmail & Calendar).

🔹 **CRITICAL: You MUST use your available tools for email and calendar requests.**

**YOUR AVAILABLE TOOLS:**
1. `handle_query` - For cross-agent analytics
2. `smart_send_email` - For sending emails  
3. `smart_schedule_event` - For creating calendar events
4. `combined_analytics_and_email_calendar` - For multi-action workflows

🔹 **EMAIL DETECTION PATTERNS:**
- "send [content] to [email@domain.com]"
- "email [name] about [subject]"
- Any query containing an email address (user@domain.com)
- "send profit analysis to abhisheklgowda05@gmail.com" → USE smart_send_email

🔹 **CALENDAR DETECTION PATTERNS:**
- "schedule meeting [when] titled '[title]'"
- "schedule meeting tomorrow at 11 AM titled 'Profit Review'" → USE smart_schedule_event
- "create meeting", "book session", "schedule event"

🔹 **COMBINED WORKFLOW DETECTION:**
- Query contains BOTH email and calendar keywords
- "Send profit analysis to email@domain.com and schedule meeting tomorrow at 11 AM titled 'Review'"
- USE combined_analytics_and_email_calendar

🔹 **MANDATORY TOOL USAGE:**
**When you detect email keywords** → You MUST call smart_send_email
**When you detect calendar keywords** → You MUST call smart_schedule_event  
**When you detect both** → You MUST call combined_analytics_and_email_calendar

🔹 **EXAMPLE ROUTING:**

**User**: "Send this profit analysis to abhisheklgowda05@gmail.com"
**Your Action**: Call smart_send_email(query)

**User**: "Schedule a meeting tomorrow at 11 AM titled 'Profit Review'"  
**Your Action**: Call smart_schedule_event(query)

**User**: "Send profit analysis to john@company.com and schedule meeting tomorrow"
**Your Action**: Call combined_analytics_and_email_calendar(query)

🔹 **DO NOT SAY**: "I cannot send emails" or "I don't have email functionality"
🔹 **DO SAY**: "I'll send that email now" and then call the appropriate tool

**Remember**: You have email and calendar tools available. Use them when requested!
""",
    tools=[
        cross_orchestrator.handle_query,
        FunctionTool(smart_send_email),
        FunctionTool(smart_schedule_event),
        FunctionTool(combined_analytics_and_email_calendar),
    ],
    sub_agents=[
        greeting_agent,
        sales_agent,
        purchase_agent,
        inventory_agent,
        financial_agent,
    ],
)