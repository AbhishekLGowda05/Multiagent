import os
import sys
import json
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from .cross_agent_orchestrator import CrossAgentOrchestrator, DEFAULT_SPECS

from manager.sub_agents.sales_agent.agent import sales_agent
from manager.sub_agents.greeting_agent.agent import greeting_agent
from manager.sub_agents.purchase_agent.agent import purchase_agent
from manager.sub_agents.inventory_agent.agent import inventory_agent
from manager.sub_agents.financial_agent.agent import financial_agent

# Add the parent directory to sys.path to access google_utils
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import Google utilities with better error handling
try:
    from google_utils.gmail_tools import send_email
    from google_utils.calendar_tools import create_event
    GOOGLE_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google utilities not available: {e}")
    
    def send_email(to_email: str, subject: str, body: str) -> dict:
        return {
            "status": "demo_mode",
            "message": f"📧 Email would be sent to {to_email}",
            "subject": subject,
            "to": to_email,
            "body": body[:100] + "..." if len(body) > 100 else body,
            "note": "Demo mode - Google credentials not configured"
        }
    
    def create_event(title: str, start_time: str, end_time: str) -> dict:
        return {
            "status": "demo_mode",
            "message": f"📅 Calendar event '{title}' would be created",
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "note": "Demo mode - Google credentials not configured"
        }
    
    GOOGLE_UTILS_AVAILABLE = False

import re
from datetime import datetime, timedelta
from typing import Any

# Session memory for last analytics result
LAST_ANALYTICS_RESULT: str = ""

def set_last_analytics_result(result: Any) -> None:
    """Store the latest analytics result for follow-up commands."""
    global LAST_ANALYTICS_RESULT
    try:
        if isinstance(result, str):
            LAST_ANALYTICS_RESULT = result
        else:
            LAST_ANALYTICS_RESULT = json.dumps(result, indent=2)
    except Exception:
        LAST_ANALYTICS_RESULT = str(result)

# Initialize cross-agent orchestrator
cross_orchestrator = CrossAgentOrchestrator(DEFAULT_SPECS)

def handle_query_with_memory(query: str) -> Any:
    """Wrapper around cross_orchestrator.handle_query that stores the result."""
    result = cross_orchestrator.handle_query(query)
    set_last_analytics_result(result)
    return result

def smart_send_email(query: str) -> Any:
    """Email helper that understands analytics context and remembers results."""
    print(f"[LOG] smart_send_email triggered with query: {query}")

    # "send this to user@example.com"
    match_send_this = re.search(r"send this to ([\w.+-]+@[\w.-]+\.\w+)", query, re.I)
    if match_send_this:
        to_email = match_send_this.group(1)
        subject = "Business Report"
        body = LAST_ANALYTICS_RESULT or "No analytics result available"
        return send_email(to_email, subject, body)

    # "send report to user@example.com"
    match_send_to = re.search(r"send (.+?) to ([\w.+-]+@[\w.-]+\.\w+)", query, re.I)
    if match_send_to:
        subject_text, to_email = match_send_to.groups()
        if subject_text.strip().lower() == "this":
            subject = "Business Report"
            body = LAST_ANALYTICS_RESULT or "No analytics result available"
        else:
            subject = subject_text.strip().title()
            body = f"Hi,\n\nPlease find the {subject_text} as requested.\n\nBest regards"
        return send_email(to_email, subject, body)

    # "email John about quarterly results" or "send email to john@example.com about sales"
    match_about = re.search(r"(?:send (?:an )?email to|email) ([\w.+-]+@[\w.-]+\.\w+|[\w\s]+) about (.+)", query, re.I)
    if match_about:
        recipient, subject_text = match_about.groups()
        to_email = recipient if "@" in recipient else f"{recipient.lower().replace(' ', '')}@example.com"
        subject = subject_text.strip()
        body = f"Hi,\n\nRegarding: {subject}\n\nPlease find the requested information.\n\nBest regards"
        return send_email(to_email, subject, body)

    # Generic email detection
    email_match = re.search(r"([\w.+-]+@[\w.-]+\.\w+)", query)
    if email_match:
        to_email = email_match.group(1)
        subject_search = re.search(r"(?:about|subject|titled|regarding) ['\"]?([^'\"]+)['\"]?", query, re.I)
        if subject_search:
            subject = subject_search.group(1).strip()
            body = f"Hi,\n\nRegarding: {subject}\n\nPlease find the requested information.\n\nBest regards"
        else:
            subject = "Business Report"
            body = LAST_ANALYTICS_RESULT or "No analytics result available"
        return send_email(to_email, subject, body)

    # "email John" with no subject
    match_name_only = re.search(r"email (\w+)\b", query, re.I)
    if match_name_only:
        name = match_name_only.group(1)
        to_email = f"{name.lower()}@example.com"
        subject = "Business Report"
        body = LAST_ANALYTICS_RESULT or "No analytics result available"
        return send_email(to_email, subject, body)

    return {
        "status": "error",
        "message": "Could not parse email command. Please provide recipient email or name.",
        "examples": [
            "send report to user@email.com",
            "email John about quarterly results",
            "send profit analysis to manager@company.com"
        ],
    }

def smart_schedule_event(query: str) -> Any:
    """Parse meeting requests and create calendar events."""
    print(f"[LOG] smart_schedule_event triggered with query: {query}")

    base_date = datetime.now()

    def parse_month(month_str: str) -> int:
        months = {
            "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
            "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
            "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9,
            "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
        }
        return months.get(month_str.lower(), datetime.now().month)

    # Patterns
    relative_pattern = re.search(
        r"schedule (?:a )?meeting (today|tomorrow) at (\d+)(?::(\d+))?\s*(am|pm)(?: titled ['\"](.+?)['\"])?",
        query,
        re.I,
    )
    date_first = re.search(
        r"schedule (?:a )?meeting (?:with [\w\s]+)?on (\d{1,2})(?:st|nd|rd|th)?(?: of)? (\w+) at (\d+)(?::(\d+))?\s*(am|pm)",
        query,
        re.I,
    )
    time_first = re.search(
        r"schedule (?:a )?meeting .*?at (\d+)(?::(\d+))?\s*(am|pm) on (\d{1,2})(?:st|nd|rd|th)?(?: of)? (\w+)",
        query,
        re.I,
    )

    match = relative_pattern or date_first or time_first
    if not match:
        return {
            "status": "error",
            "message": "Could not parse calendar command. Please specify day and time in a clearer format.",
            "examples": [
                "schedule meeting tomorrow at 2 PM",
                "schedule meeting on 31st of July at 7 PM",
                "schedule meeting at 7 PM on 31st of July",
                "schedule meeting tomorrow at 11 AM titled 'Review'",
            ],
        }

    if match is relative_pattern:
        day, start_hour, start_min, period, title = relative_pattern.groups()
        if day.lower() == "tomorrow":
            base_date += timedelta(days=1)
        start_hour = int(start_hour)
        if period.lower() == "pm" and start_hour != 12:
            start_hour += 12
        elif period.lower() == "am" and start_hour == 12:
            start_hour = 0
        start_time = base_date.replace(hour=start_hour, minute=int(start_min or 0), second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        meeting_title = title or "Business Meeting"
    else:
        if match is date_first:
            day, month, start_hour, start_min, period = date_first.groups()
        else:
            start_hour, start_min, period, day, month = time_first.groups()
        month_num = parse_month(month)
        day_num = int(day)
        year = base_date.year
        target_date = datetime(year, month_num, day_num)
        if target_date < base_date:
            target_date = datetime(year + 1, month_num, day_num)
        start_hour = int(start_hour)
        if period.lower() == "pm" and start_hour != 12:
            start_hour += 12
        elif period.lower() == "am" and start_hour == 12:
            start_hour = 0
        start_time = target_date.replace(hour=start_hour, minute=int(start_min or 0), second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        meeting_title = "Business Meeting"

    if "sales" in query.lower():
        meeting_title = "Sales Review Meeting"

    return create_event(meeting_title, start_time.isoformat() + "Z", end_time.isoformat() + "Z")

def combined_analytics_and_email_calendar(query: str) -> Any:
    """Handle queries that combine analytics with email and/or calendar actions."""
    results = {}
    
    # Check if query contains email and/or calendar actions
    has_email = any(keyword in query.lower() for keyword in ["send", "email", "@"])
    has_calendar = any(keyword in query.lower() for keyword in ["schedule", "meeting", "calendar"])
    has_analysis = any(keyword in query.lower() for keyword in ["profit", "analysis", "report", "sales", "financial", "summary"])
    
    if has_analysis and (has_email or has_calendar):
        # First perform analysis if requested
        if has_analysis:
            try:
                analysis_result = handle_query_with_memory(query)
                results["analysis_result"] = analysis_result
                results["analysis_status"] = "✅ Analysis completed successfully"
            except Exception as e:
                results["analysis_error"] = f"❌ Analysis failed: {str(e)}"

        # Handle email
        if has_email:
            try:
                email_result = smart_send_email(query)
                results["email_result"] = email_result
                if email_result.get("status") == "demo_mode":
                    results["email_status"] = "📧 Email prepared (demo mode - configure Google credentials to send)"
                else:
                    results["email_status"] = "✅ Email sent successfully"
            except Exception as e:
                results["email_error"] = f"❌ Email failed: {str(e)}"

        # Handle calendar
        if has_calendar:
            try:
                calendar_result = smart_schedule_event(query)
                results["calendar_result"] = calendar_result
                if isinstance(calendar_result, dict) and calendar_result.get("status") == "demo_mode":
                    results["calendar_status"] = "📅 Calendar event prepared (demo mode - configure Google credentials to create)"
                elif isinstance(calendar_result, dict) and calendar_result.get("status") == "error":
                    results["calendar_status"] = f"❌ Calendar parsing failed: {calendar_result.get('message')}"
                else:
                    results["calendar_status"] = "✅ Calendar event scheduled successfully"
            except Exception as e:
                results["calendar_error"] = f"❌ Calendar failed: {str(e)}"

        # Summary message
        success_count = sum(1 for key in results.keys() if key.endswith("_status") and "✅" in results[key])
        total_actions = len([k for k in results.keys() if k.endswith("_status")])

        results["summary"] = f"Workflow completed: {success_count}/{total_actions} actions successful"
        return results

    return {
        "status": "error",
        "message": "Could not parse combined workflow command"
    }

root_agent = Agent(
    name="manager",
    model="gemini-2.0-flash",
    description="Central orchestrator for analytics requests with Google integration",
    instruction="""
You are the Manager Orchestrator for a multi-agent analytics system with full Google Workspace integration (Gmail & Calendar). 
Your job is to route analytics queries to the right agents AND handle email/calendar actions using the provided tools.

🚨 **CRITICAL:**
- You MUST call `smart_send_email`, `smart_schedule_event`, or `combined_analytics_and_email_calendar` whenever email or calendar intent is detected.
- Never reply with plain text when an email or meeting is requested.
- Never say "I cannot send emails" or "I cannot schedule meetings". Always invoke the tool.

---

## 📧 EMAIL RULES:
- If a query contains an email address (e.g. user@domain.com) → Call `smart_send_email`
- If the user says "send this to ..." → Call `smart_send_email` and include the last analytics result as the email body.
- Keywords: send, email, mail, forward, share, report, analysis, summary.

✅ Example:
User: "Send this to abhisheklgowda05@gmail.com"
➡️ Action: `smart_send_email(query)` with previous analytics output as the content.

---

## 📅 CALENDAR RULES:
- If query contains "schedule", "meeting", "create event", "book session" → Call `smart_schedule_event`
- Parse natural language date/time ("tomorrow", "31st of July", "7 PM") into ISO format.
- If only start time is given, default meeting length = 1 hour.

✅ Example:
User: "Schedule a meeting on 31st of July at 7 PM"
➡️ Action: `smart_schedule_event(query)`

---

## 🔄 COMBINED WORKFLOW:
- If a query contains BOTH email and calendar intent → Call `combined_analytics_and_email_calendar`
- First perform analytics if requested, then send email and/or schedule the event.

✅ Example:
User: "Send profit report to cfo@company.com and schedule review meeting tomorrow at 11 AM"
➡️ Action: `combined_analytics_and_email_calendar(query)`

---

## 🚀 MANDATORY TOOL USAGE:
1. Email intent detected → Always call `smart_send_email`
2. Calendar intent detected → Always call `smart_schedule_event`
3. Both detected → Always call `combined_analytics_and_email_calendar`

Gemini 2.0 Flash must ALWAYS trigger a tool, not a plain response.

---

## 🔍 RESPONSE FORMAT:
- After tool execution, confirm action:  
  📧 "✅ Email sent to {recipient}"  
  📅 "✅ Meeting scheduled for {time}"
- For follow-up "send this" commands, include the last analytics result in the email body automatically.

---

## 🎯 PURPOSE:
- Deliver analytics + integrate Gmail & Calendar seamlessly.
- Act as a complete business assistant combining insights, communication, and scheduling.
""",

    tools=[
        FunctionTool(handle_query_with_memory),
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