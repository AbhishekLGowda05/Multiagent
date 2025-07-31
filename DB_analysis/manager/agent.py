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
    
    def create_event(
        title: str, start_time: str, end_time: str, description: str | None = None
    ) -> dict:
        event = {

            "status": "demo_mode",
            "message": f"📅 Calendar event '{title}' would be created",
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "note": "Demo mode - Google credentials not configured",

        }
        if description is not None:
            event["description"] = description
        return event
    
    GOOGLE_UTILS_AVAILABLE = False

import re
from datetime import datetime, timedelta
from typing import Any

# Rest of your code remains the same...
cross_orchestrator = CrossAgentOrchestrator(DEFAULT_SPECS)

# Enhanced Google integration tools with better pattern matching
def smart_send_email(query: str, body_override: str | None = None) -> Any:
    """Enhanced email tool that can handle business analytics context.

    Parameters
    ----------
    query : str
        Natural language command containing email details.
    body_override : str | None, optional
        When provided, this text will be used as the email body instead
        of the automatically generated content.
    """
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
        body_final = body_override if body_override is not None else body
        return send_email(to_email, subject, body_final)
    
    elif pattern3:
        to_recipient, subject = pattern3.groups()
        # Check if it's an email address or name
        if "@" in to_recipient:
            to_email = to_recipient
        else:
            to_email = f"{to_recipient.lower().replace(' ', '')}@example.com"
        body = f"Hi,\n\nRegarding: {subject}\n\nPlease find the requested information attached.\n\nBest regards"
        body_final = body_override if body_override is not None else body
        return send_email(to_email, subject, body_final)
    
    elif pattern4:
        # Found email address in query
        to_email = pattern4.group(1)
        if "profit" in query.lower():
            subject = "Profit Analysis Report"
            body = "Hi,\n\nPlease find the profit analysis report as requested.\n\nBest regards"
        else:
            subject = "Business Report"
            body = "Hi,\n\nPlease find the requested business analysis.\n\nBest regards"
        body_final = body_override if body_override is not None else body
        return send_email(to_email, subject, body_final)
    
    elif pattern2:
        to_name, subject = pattern2.groups()
        to_email = f"{to_name.lower()}@example.com"
        body = f"Hi {to_name},\n\nRegarding: {subject}\n\nPlease find the requested information.\n\nBest regards"
        body_final = body_override if body_override is not None else body
        return send_email(to_email, subject, body_final)
    
    else:
        raise ValueError("Could not parse email command. Please provide recipient email or name.")

def smart_schedule_event(query: str, description: str | None = None) -> Any:
    """Enhanced calendar tool for business meetings and analytics sessions.

    Parameters
    ----------
    query : str
        Natural language command describing the meeting.
    description : str | None, optional
        Optional description to include in the calendar event.
    """
    # Pattern 1: "Schedule [meeting] for [day] at [time]" or "schedule a meeting tomorrow at 11 AM titled 'Title'"
    pattern1 = re.search(r"schedule (?:a )?(?:meeting )?(.+?) (?:for |on )?(today|tomorrow|monday|tuesday|wednesday|thursday|friday) at (\d+)(?::(\d+))?\s*(am|pm)(?:\s*titled\s*['\"](.+?)['\"])?", query, re.I)
    # Pattern 2: "Create meeting [subject] tomorrow from [time] to [time]"
    pattern2 = re.search(r"create (?:meeting |event )?(.+?) (today|tomorrow) from (\d+)\s*(am|pm) to (\d+)\s*(am|pm)", query, re.I)
    # Pattern 3: Enhanced pattern for "schedule meeting tomorrow at 11 AM titled 'Title'"
    pattern3 = re.search(r"schedule (?:a )?meeting (today|tomorrow) at (\d+)(?::(\d+))?\s*(am|pm) titled ['\"](.+?)['\"]", query, re.I)
    # Pattern 4: "Book [meeting type] session [when]"
    pattern4 = re.search(r"book (.+?) session (today|tomorrow)", query, re.I)
    # Pattern 5: "schedule meeting with [name] on [date] at [time]" - NEW PATTERN
    pattern5 = re.search(r"schedule (?:a )?meeting (?:with [\w\s]+)?on (\d{1,2})(?:st|nd|rd|th)? of (\w+) at (\d+)(?::(\d+))?\s*(am|pm)", query, re.I)
    # Pattern 6: Generic date pattern "schedule meeting [date] at [time]"
    pattern6 = re.search(r"schedule (?:a )?meeting.+?(\d{1,2})(?:st|nd|rd|th)? (?:of )?(\w+) at (\d+)(?::(\d+))?\s*(am|pm)", query, re.I)
    
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
    
    # Check new patterns first (date-specific)
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
        
        return create_event(
            meeting_title,
            start_time.isoformat() + "Z",
            end_time.isoformat() + "Z",
            description=description,
        )
    
    elif pattern6:
        day, month, start_hour, start_min, start_period = pattern6.groups()
        
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
        
        return create_event(
            meeting_title,
            start_time.isoformat() + "Z",
            end_time.isoformat() + "Z",
            description=description,
        )
    
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
        end_time = start_time + timedelta(hours=1)  # Default 1 hour meeting
        
        return create_event(
            meeting_type,
            start_time.isoformat() + "Z",
            end_time.isoformat() + "Z",
            description=description,
        )
    
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
        
        return create_event(
            meeting_type.title(),
            start_time.isoformat() + "Z",
            end_time.isoformat() + "Z",
            description=description,
        )
    
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
        
        return create_event(
            meeting_type.title(),
            start_time.isoformat() + "Z",
            end_time.isoformat() + "Z",
            description=description,
        )
    
    elif pattern4:
        session_type, day = pattern4.groups()
        
        if day.lower() == "tomorrow":
            base_date += timedelta(days=1)
        
        # Default to 2 PM - 3 PM for sessions
        start_time = base_date.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        return create_event(
            f"{session_type.title()} Session",
            start_time.isoformat() + "Z",
            end_time.isoformat() + "Z",
            description=description,
        )
    
    else:
        # If no patterns match, try to extract basic date/time info
        time_match = re.search(r"(\d+)(?::(\d+))?\s*(am|pm)", query, re.I)
        date_match = re.search(r"(\d{1,2})(?:st|nd|rd|th)? (?:of )?(\w+)", query, re.I)
        
        if time_match and date_match:
            # Extract time
            hour, minute, period = time_match.groups()
            hour = int(hour)
            if period.lower() == "pm" and hour != 12:
                hour += 12
            elif period.lower() == "am" and hour == 12:
                hour = 0
            
            # Extract date
            day, month = date_match.groups()
            month_num = parse_month(month)
            day_num = int(day)
            year = datetime.now().year
            
            # If the date has passed this year, use next year
            target_date = datetime(year, month_num, day_num)
            if target_date < datetime.now():
                target_date = datetime(year + 1, month_num, day_num)
            
            start_time = target_date.replace(hour=hour, minute=int(minute or 0), second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            meeting_title = "Business Meeting"
            if "sales" in query.lower():
                meeting_title = "Sales Review Meeting"
            
            return create_event(
                meeting_title,
                start_time.isoformat() + "Z",
                end_time.isoformat() + "Z",
                description=description,
            )
        
        return {
            "status": "error",
            "message": "Could not parse calendar command. Please specify day and time in a clearer format.",
            "examples": [
                "schedule meeting tomorrow at 2 PM",
                "schedule meeting on 31st of July at 7 PM",
                "create meeting today from 10 AM to 11 AM"
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
        summary_text = None

        if has_analysis:
            try:
                analysis_result = cross_orchestrator.handle_query(query)
                results["analysis_result"] = analysis_result
                results["analysis_status"] = "✅ Analysis completed successfully"

                # Create a short text summary from cross-agent analysis
                summary_lines = []
                analysis_meta = analysis_result.get("_metadata", {}).get(
                    "cross_agent_analysis", {}
                )
                if analysis_meta:
                    if analysis_meta.get("summary"):
                        summary_lines.append(f"- {analysis_meta['summary']}")
                    for item in analysis_meta.get("key_findings", []):
                        summary_lines.append(f"- {item}")
                    for item in analysis_meta.get("recommendations", []):
                        summary_lines.append(f"- {item}")
                summary_text = "\n".join(summary_lines) if summary_lines else None
                results["analysis_summary"] = summary_text
            except Exception as e:
                results["analysis_error"] = f"❌ Analysis failed: {str(e)}"

        # Handle email
        if has_email:
            try:
                email_result = smart_send_email(query, body_override=summary_text)
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
                calendar_result = smart_schedule_event(query, description=summary_text)
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