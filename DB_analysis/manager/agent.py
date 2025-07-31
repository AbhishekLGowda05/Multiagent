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

# Initialize cross-agent orchestrator
cross_orchestrator = CrossAgentOrchestrator(DEFAULT_SPECS)

def smart_send_email(query: str) -> Any:
    """Enhanced email tool that can handle business analytics context."""
    print(f"[LOG] smart_send_email triggered with query: {query}")
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
        elif "sales" in query.lower():
            subject = "Sales Analysis Report"
            body = "Hi,\n\nPlease find the sales analysis report as requested.\n\nBest regards"
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
        return {
            "status": "error",
            "message": "Could not parse email command. Please provide recipient email or name.",
            "examples": [
                "send report to user@email.com",
                "email John about quarterly results",
                "send profit analysis to manager@company.com"
            ]
        }

def smart_schedule_event(query: str) -> Any:
    """Enhanced calendar tool for business meetings and analytics sessions."""
    print(f"[LOG] smart_schedule_event triggered with query: {query}")
    # Pattern for "schedule meeting with [name] on 31st of July at 7pm"
    pattern5 = re.search(r"schedule (?:a )?meeting (?:with [\w\s]+)?on (\d{1,2})(?:st|nd|rd|th)? of (\w+) at (\d+)(?::(\d+))?\s*(am|pm)", query, re.I)
    # Pattern where time comes before the date, e.g. "schedule meeting at 7 PM on 31st of July"
    pattern_time_first = re.search(r"schedule (?:a )?meeting .*?at (\d+)(?::(\d+))?\s*(am|pm) on (\d{1,2})(?:st|nd|rd|th)? of (\w+)", query, re.I)
    # Pattern for "schedule meeting tomorrow at 11 AM titled 'Title'"
    pattern3 = re.search(r"schedule (?:a )?meeting (today|tomorrow) at (\d+)(?::(\d+))?\s*(am|pm) titled ['\"](.+?)['\"]", query, re.I)
    # Pattern for "schedule meeting at 7 PM on 31st of July"
    pattern_time_first = re.search(
        r"at (\d+)(?::(\d+))?\s*(am|pm) on (\d{1,2})(?:st|nd|rd|th)?(?: of)? (\w+)",
        query,
        re.I,
    )

    # General pattern for date and time
    pattern_general = re.search(r"schedule (?:a )?meeting.+?(\d{1,2})(?:st|nd|rd|th)? (?:of )?(\w+) at (\d+)(?::(\d+))?\s*(am|pm)", query, re.I)
    
    base_date = datetime.now()
    
    def parse_month(month_str):
        """Helper function to parse month names to numbers."""
        months = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
            'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        return months.get(month_str.lower(), datetime.now().month)
    
    # Check for specific date patterns first
    if pattern5:
        day, month, start_hour, start_min, start_period = pattern5.groups()
        
        # Parse the specific date
        month_num = parse_month(month)
        day_num = int(day)
        year = datetime.now().year
        
        # If the date has passed this year, use next year
        target_date = datetime(year, month_num, day_num)
        if target_date < datetime.now():
            target_date = datetime(year + 1, month_num, day_num)
        
        # Parse time
        start_hour = int(start_hour)
        if start_period.lower() == "pm" and start_hour != 12:
            start_hour += 12
        elif start_period.lower() == "am" and start_hour == 12:
            start_hour = 0
        
        start_time = target_date.replace(hour=start_hour, minute=int(start_min or 0), second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        # Extract meeting title from query
        meeting_title = "Business Meeting"
        if "sales" in query.lower():
            meeting_title = "Sales Review Meeting"
        
        return create_event(meeting_title, start_time.isoformat() + "Z", end_time.isoformat() + "Z")

    elif pattern_time_first:
        start_hour, start_min, start_period, day, month = pattern_time_first.groups()

        month_num = parse_month(month)
        day_num = int(day)
        year = datetime.now().year

        target_date = datetime(year, month_num, day_num)
        if target_date < datetime.now():
            target_date = datetime(year + 1, month_num, day_num)

        start_hour = int(start_hour)
        if start_period.lower() == "pm" and start_hour != 12:
            start_hour += 12
        elif start_period.lower() == "am" and start_hour == 12:
            start_hour = 0

        start_time = target_date.replace(hour=start_hour, minute=int(start_min or 0), second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        meeting_title = "Business Meeting"
        if "sales" in query.lower():
            meeting_title = "Sales Review Meeting"

        return create_event(meeting_title, start_time.isoformat() + "Z", end_time.isoformat() + "Z")
    
    elif pattern_time_first:
        start_hour, start_min, start_period, day, month = pattern_time_first.groups()


        month_num = parse_month(month)
        day_num = int(day)
        year = datetime.now().year

        target_date = datetime(year, month_num, day_num)
        if target_date < datetime.now():
            target_date = datetime(year + 1, month_num, day_num)

        start_hour = int(start_hour)
        if start_period.lower() == "pm" and start_hour != 12:
            start_hour += 12
        elif start_period.lower() == "am" and start_hour == 12:
            start_hour = 0

        start_time = target_date.replace(hour=start_hour, minute=int(start_min or 0), second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        meeting_title = "Business Meeting"
        if "sales" in query.lower():
            meeting_title = "Sales Review Meeting"

        return create_event(meeting_title, start_time.isoformat() + "Z", end_time.isoformat() + "Z")

    elif pattern_general:
        day, month, start_hour, start_min, start_period = pattern_general.groups()
        
        # Parse the specific date
        month_num = parse_month(month)
        day_num = int(day)
        year = datetime.now().year
        
        # If the date has passed this year, use next year
        target_date = datetime(year, month_num, day_num)
        if target_date < datetime.now():
            target_date = datetime(year + 1, month_num, day_num)
        
        # Parse time
        start_hour = int(start_hour)
        if start_period.lower() == "pm" and start_hour != 12:
            start_hour += 12
        elif start_period.lower() == "am" and start_hour == 12:
            start_hour = 0
        
        start_time = target_date.replace(hour=start_hour, minute=int(start_min or 0), second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        # Extract meeting title from query
        meeting_title = "Business Meeting"
        if "sales" in query.lower():
            meeting_title = "Sales Review Meeting"
        
        return create_event(meeting_title, start_time.isoformat() + "Z", end_time.isoformat() + "Z")
    
    elif pattern3:
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
        end_time = start_time + timedelta(hours=1)
        
        return create_event(meeting_type, start_time.isoformat() + "Z", end_time.isoformat() + "Z")
    
    else:
        return {
            "status": "error",
            "message": "Could not parse calendar command. Please specify day and time in a clearer format.",
            "examples": [
                "schedule meeting tomorrow at 2 PM",
                "schedule meeting on 31st of July at 7 PM",
                "schedule meeting at 7 PM on 31st of July",
                "schedule meeting tomorrow at 11 AM titled 'Review'"
            ]
        }

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
                analysis_result = cross_orchestrator.handle_query(query)
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