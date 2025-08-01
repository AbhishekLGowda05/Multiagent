from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
import os, sys, re, json
from datetime import datetime, timedelta
from typing import Any

# ✅ Add Int-Assignment root path so google_utils is discoverable
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))  # Goes up to📌 **MANDATORY BEHAVIOR:**

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ✅ Import Google utilities (now will work inside ADK)
from google_utils.gmail_tools import send_email
from google_utils.calendar_tools import (
    create_event,
    create_recurring_event,
    build_daily_rrule,
    build_interval_rrule,
)

# Chart generation utility
from visualization_utils import generate_chart

# ✅ Import sub-agents
from manager.sub_agents.sales_agent.agent import sales_agent
from manager.sub_agents.greeting_agent.agent import greeting_agent
from manager.sub_agents.purchase_agent.agent import purchase_agent
from manager.sub_agents.inventory_agent.agent import inventory_agent
from manager.sub_agents.financial_agent.agent import financial_agent

# ✅ Cross-agent orchestrator
from .cross_agent_orchestrator import CrossAgentOrchestrator, DEFAULT_SPECS
cross_orchestrator = CrossAgentOrchestrator(DEFAULT_SPECS)

# ✅ Memory for last analytics result
LAST_ANALYTICS_RESULT: str = ""

# Utility helpers for enhanced email output
def generate_chart(data: list[float] | None = None, path: str = "chart.png") -> str:
    """Create a simple chart from numeric data and return the file path."""
    import matplotlib.pyplot as plt

    values = data or [1, 2, 3, 4]
    plt.figure()
    plt.plot(range(1, len(values) + 1), values, marker="o")
    plt.title("Analytics Chart")
    plt.xlabel("Index")
    plt.ylabel("Value")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def _create_pdf(text: str, chart_path: str, pdf_path: str = "report.pdf") -> str:
    """Generate a simple PDF containing text and an optional chart."""
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(pdf_path) as pdf:
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")
        ax.text(0.05, 0.95, text, va="top", wrap=True)
        pdf.savefig(fig)
        plt.close(fig)

        if os.path.exists(chart_path):
            img = plt.imread(chart_path)
            fig, ax = plt.subplots()
            ax.imshow(img)
            ax.axis("off")
            pdf.savefig(fig)
            plt.close(fig)
    return pdf_path


def _send_email_html(
    to_email: str, subject: str, html_body: str, attachments: list[str] | None = None
) -> Any:
    """Send an HTML email with optional attachments using Gmail API."""
    import base64
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    from googleapiclient.discovery import build
    from google_utils.auth import get_credentials

    creds = get_credentials(["https://www.googleapis.com/auth/gmail.send"])
    service = build("gmail", "v1", credentials=creds)

    message = MIMEMultipart()
    message["To"] = to_email
    message["From"] = "me"
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    for path in attachments or []:
        with open(path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(path))
        part["Content-Disposition"] = f"attachment; filename={os.path.basename(path)}"
        message.attach(part)

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {"raw": encoded_message}
    return service.users().messages().send(userId="me", body=create_message).execute()

def set_last_analytics_result(result):
    """Store analytics result in global memory with enhanced debugging."""
    global LAST_ANALYTICS_RESULT
    print(f"[DEBUG] ===== STORING ANALYTICS RESULT =====")
    print(f"[DEBUG] Input type: {type(result)}")
    print(f"[DEBUG] Input length: {len(str(result))}")
    print(f"[DEBUG] Input preview: {str(result)[:200]}...")
    
    if isinstance(result, str):
        LAST_ANALYTICS_RESULT = result
    else:
        LAST_ANALYTICS_RESULT = str(result)
    
    print(f"[DEBUG] Stored LAST_ANALYTICS_RESULT length: {len(LAST_ANALYTICS_RESULT)}")
    print(f"[DEBUG] Stored LAST_ANALYTICS_RESULT preview: {LAST_ANALYTICS_RESULT[:200]}...")
    print(f"[DEBUG] ===== STORAGE COMPLETED =====")
    
    # Verification
    if len(LAST_ANALYTICS_RESULT) == 0:
        print(f"[ERROR] LAST_ANALYTICS_RESULT is empty after storage!")
    else:
        print(f"[SUCCESS] LAST_ANALYTICS_RESULT stored successfully")

# 🔹 Analytics handler
def handle_query_with_memory(query: str) -> str:
    result = cross_orchestrator.handle_query(query)
    set_last_analytics_result(result)
    return result

# 🔹 NEW: Function to capture actual agent responses for email formatting
def format_and_store_agent_response(response: str) -> str:
    """Format agent response and store it for email use."""
    print(f"[DEBUG] ===== FORMATTING AGENT RESPONSE =====")
    print(f"[DEBUG] Response type: {type(response)}")
    print(f"[DEBUG] Response length: {len(str(response))}")
    print(f"[DEBUG] Response preview: {str(response)[:300]}...")
    
    # Determine report type from the response content
    response_str = str(response).lower()
    if any(word in response_str for word in ["sales", "invoice", "customer", "voucher"]):
        report_type = "SALES SUMMARY"
        emoji = "📊"
    elif any(word in response_str for word in ["financial", "profit", "revenue", "expense"]):
        report_type = "FINANCIAL ANALYSIS"
        emoji = "💰"
    elif any(word in response_str for word in ["inventory", "stock", "item"]):
        report_type = "INVENTORY ANALYSIS"
        emoji = "📦"
    elif any(word in response_str for word in ["purchase", "vendor", "supplier"]):
        report_type = "PURCHASE ANALYSIS"
        emoji = "🛒"
    else:
        report_type = "BUSINESS ANALYSIS"
        emoji = "📊"
    
    # Create formatted email body that matches ADK web display
    formatted_result = f"""{emoji} {report_type} REPORT
{'=' * (len(report_type) + 10)}

{str(response)}

{'=' * 40}
Report generated successfully ✅
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    print(f"[DEBUG] Formatted result length: {len(formatted_result)}")
    print(f"[DEBUG] Formatted result preview: {formatted_result[:300]}...")
    
    # Store for email use
    set_last_analytics_result(formatted_result)
    print(f"[DEBUG] ===== FORMATTING COMPLETED =====")
    
    return response

# 🔹 ENHANCED: Direct analytics function that ensures capture and proper formatting
def get_analytics_and_store(query: str) -> str:
    """Store analytics query for delegation and format results for email use."""
    print(f"[DEBUG] ===== ANALYTICS FUNCTION CALLED =====")
    print(f"[DEBUG] Query: {query}")
    
    # Don't call sub-agents directly - let ADK handle delegation
    # Instead, just format and store the query information
    
    # Determine report type for formatting
    if "sales" in query.lower():
        report_type = "SALES SUMMARY"
        emoji = "📊"
    elif "financial" in query.lower() or "profit" in query.lower():
        report_type = "FINANCIAL ANALYSIS"
        emoji = "💰"
    elif "inventory" in query.lower():
        report_type = "INVENTORY ANALYSIS"
        emoji = "📦"
    elif "purchase" in query.lower():
        report_type = "PURCHASE ANALYSIS"
        emoji = "🛒"
    else:
        report_type = "BUSINESS ANALYSIS"
        emoji = "📊"
    
    print(f"[DEBUG] Report type determined: {report_type}")
    
    # Store query information temporarily - actual result will be captured after delegation
    query_info = f"Analytics query received: {query}\nReport type: {report_type}\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    set_last_analytics_result(query_info)
    
    print(f"[DEBUG] Query info stored temporarily")
    print(f"[DEBUG] ===== ANALYTICS FUNCTION COMPLETED =====")
    
    # Return the query to trigger normal ADK delegation
    return query

# 🔹 NEW: Auto-capture function for sub-agent delegation (simplified signature)
def capture_sub_agent_result(result: str) -> str:
    """Capture and format sub-agent results for memory storage."""
    print(f"[DEBUG] Capturing sub-agent result: {type(result)}")
    
    # Format result for email use
    if result:
        formatted_result = f"📊 BUSINESS ANALYSIS REPORT\n{'=' * 35}\n\n{str(result)}\n\n{'=' * 20}\nReport generated successfully ✅"
        set_last_analytics_result(formatted_result)
    
    return result

# 🔹 FIXED: Email tool with proper pattern matching and enhanced debugging
def smart_send_email(query: str, analytics_data: dict | None = None) -> dict:
    """Send email based on natural language query with memory of last analytics result.

    If ``analytics_data`` is provided, a chart of the data will be generated and
    embedded into the email body as a base64 encoded ``<img>`` tag.

    """
    print(f"[DEBUG] ===== EMAIL FUNCTION CALLED =====")
    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] LAST_ANALYTICS_RESULT length: {len(LAST_ANALYTICS_RESULT)}")
    print(f"[DEBUG] LAST_ANALYTICS_RESULT first 500 chars: {LAST_ANALYTICS_RESULT[:500]}")
    print(f"[DEBUG] LAST_ANALYTICS_RESULT type: {type(LAST_ANALYTICS_RESULT)}")
    
    # Pattern 1: "send this to email@domain.com" or "mail this to email@domain.com"
    pattern1 = re.search(r"(?:send|mail) (?:this|these results?) to ([\w.+-]+@[\w.-]+\.\w+)", query, re.I)
    
    # Pattern 2: "send email to email@domain.com" 
    pattern2 = re.search(r"send (?:an )?email to ([\w.+-]+@[\w.-]+\.\w+)", query, re.I)
    
    # Pattern 3: Just find any email address in the query
    pattern3 = re.search(r"([\w.+-]+@[\w.-]+\.\w+)", query)
    
    to_email = None
    if pattern1:
        to_email = pattern1.group(1)
        subject = "Business Analysis Results"
        print(f"[DEBUG] Pattern 1 matched - Email: {to_email}")
    elif pattern2:
        to_email = pattern2.group(1)
        subject = "Business Report"
        print(f"[DEBUG] Pattern 2 matched - Email: {to_email}")
    elif pattern3:
        to_email = pattern3.group(1)
        subject = "Sales Summary Report"
        print(f"[DEBUG] Pattern 3 matched - Email: {to_email}")
    else:
        print(f"[DEBUG] No email pattern matched")
        return {"status": "error", "message": "No email address found in query"}
    
    # Use the stored result if available
    if LAST_ANALYTICS_RESULT and len(LAST_ANALYTICS_RESULT.strip()) > 0:
        body_text = LAST_ANALYTICS_RESULT
        print(f"[DEBUG] Using stored analytics result, length: {len(body_text)}")
    else:
        # If no analytics result, provide a helpful message
        body_text = (
            "📊 BUSINESS ANALYSIS REPORT\n\nNo analytics data was found in memory."
        )
        print(f"[DEBUG] Using fallback message")

    chart_file = generate_chart()
    attach_pdf = "pdf" in query.lower()

    html_body = f"<html><body><pre>{body_text}</pre><br><img src='cid:chart'></body></html>"

    attachments = [chart_file]
    if attach_pdf:
        pdf_path = _create_pdf(body_text, chart_file)
        attachments.append(pdf_path)

    print(f"[DEBUG] Final email body length: {len(html_body)}")
    print(f"[DEBUG] Final email body preview: {html_body[:200]}...")
    print(f"[DEBUG] Sending email with {len(attachments)} attachment(s)...")

    result = _send_email_html(to_email, subject, html_body, attachments)

    print(f"[DEBUG] send_email result: {result}")
    print(f"[DEBUG] ===== EMAIL FUNCTION COMPLETED =====")

    return result

# 🔹 FIXED: Calendar tool with proper signature
def smart_schedule_event(query: str) -> dict:
    """Schedule calendar event based on natural language query."""
    print(f"[DEBUG] Calendar tool called with: {query}")
    
    base_date = datetime.now()
    
    # Pattern 1: "at 7pm on 1st of July 2024" or "at 7:00 PM on July 1, 2025"
    pattern1 = re.search(r"at (\d{1,2})(?::(\d{1,2}))?\s*(am|pm) on (?:(\d{1,2})(?:st|nd|rd|th)?\s+of\s+)?(\w+)\s+(\d{1,2})(?:,\s*)?(\d{4})?", query, re.I)
    
    # Pattern 2: "July 1, 2025 at 7:00 PM" 
    pattern2 = re.search(r"(\w+)\s+(\d{1,2})(?:,\s*)?(\d{4})?\s+at\s+(\d{1,2})(?::(\d{1,2}))?\s*(am|pm)", query, re.I)
    
    # Pattern 3: "tomorrow at 3 PM" (existing)
    pattern3 = re.search(r"(today|tomorrow) at (\d+)(?::(\d+))?\s*(am|pm)", query, re.I)
    
    # Pattern 4: "on 31st of July at 7pm" (existing but improved)
    pattern4 = re.search(r"on (\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(\w+)(?:\s+(\d{4}))?\s+at\s+(\d+)(?::(\d+))?\s*(am|pm)", query, re.I)
    
    # Pattern 5: "at 7pm on July 1st" or "at 7:00PM on 1st July"
    pattern5 = re.search(
        r"at (\d{1,2})(?::(\d{1,2}))?\s*(am|pm) on (?:(\d{1,2})(?:st|nd|rd|th)?(?:\s+of)?\s+)?(\w+)(?:\s+(\d{4}))?",

        query,
        re.I,
    )

    def parse_month(month_str):
        """Helper function to parse month names to numbers."""
        months = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
            'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        return months.get(month_str.lower(), datetime.now().month)

    def parse_time(hour_str, minute_str, period_str):
        """Helper function to parse time."""
        hour = int(hour_str)
        minute = int(minute_str or 0)
        
        if period_str.lower() == "pm" and hour != 12:
            hour += 12
        elif period_str.lower() == "am" and hour == 12:
            hour = 0
            
        return hour, minute

    start_time = None
    
    # Try Pattern 1: "at 7pm on 1st of July 2024"
    if pattern1:
        hour_str, minute_str, period, day_str, month_str, day_alt, year_str = pattern1.groups()
        print(f"[DEBUG] Pattern 1 matched: {pattern1.groups()}")
        
        day = int(day_str or day_alt or 1)
        month = parse_month(month_str)
        year = int(year_str) if year_str else datetime.now().year
        hour, minute = parse_time(hour_str, minute_str, period)
        
        start_time = datetime(year, month, day, hour, minute)
        if start_time < datetime.now():
            start_time = start_time.replace(year=start_time.year + 1)
        
    # Try Pattern 2: "July 1, 2025 at 7:00 PM"
    elif pattern2:
        month_str, day_str, year_str, hour_str, minute_str, period = pattern2.groups()
        print(f"[DEBUG] Pattern 2 matched: {pattern2.groups()}")
        
        day = int(day_str)
        month = parse_month(month_str)
        year = int(year_str) if year_str else datetime.now().year
        hour, minute = parse_time(hour_str, minute_str, period)
        
        start_time = datetime(year, month, day, hour, minute)
        if start_time < datetime.now():
            start_time = start_time.replace(year=start_time.year + 1)
        
    # Try Pattern 3: "tomorrow at 3 PM"
    elif pattern3:
        day, hour_str, minute_str, period = pattern3.groups()
        print(f"[DEBUG] Pattern 3 matched: {pattern3.groups()}")
        
        if day.lower() == "tomorrow":
            base_date += timedelta(days=1)
        hour, minute = parse_time(hour_str, minute_str, period)
        start_time = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
    # Try Pattern 4: "on 31st of July at 7pm"
    elif pattern4:
        day_str, month_str, year_str, hour_str, minute_str, period = pattern4.groups()
        print(f"[DEBUG] Pattern 4 matched: {pattern4.groups()}")
        
        day = int(day_str)
        month = parse_month(month_str)
        year = int(year_str) if year_str else datetime.now().year
        hour, minute = parse_time(hour_str, minute_str, period)
        
        start_time = datetime(year, month, day, hour, minute)
        if start_time < datetime.now():
            start_time = start_time.replace(year=start_time.year + 1)
        
    # Try Pattern 5: "at 7pm on July 1st"
    elif pattern5:
        hour_str, minute_str, period, day_str, month_str, year_str = pattern5.groups()
        print(f"[DEBUG] Pattern 5 matched: {pattern5.groups()}")

        day = int(day_str or 1)
        if month_str.lower() == "of":
            alt = re.search(r"of\s+(\w+)(?:\s+(\d{4}))?", query, re.I)
            if alt:
                month_str = alt.group(1)
                if not year_str:
                    year_str = alt.group(2)

        month = parse_month(month_str)
        year = int(year_str) if year_str else datetime.now().year
        hour, minute = parse_time(hour_str, minute_str, period)

        start_time = datetime(year, month, day, hour, minute)
        if start_time < datetime.now():
            start_time = start_time.replace(year=start_time.year + 1)

    if start_time is None:
        print(f"[DEBUG] No patterns matched for query: {query}")
        return {
            "status": "error",
            "message": "Could not parse meeting time. Please use format like 'schedule meeting at 7:00 PM on July 1, 2025'",
            "examples": [
                "schedule meeting tomorrow at 2 PM",
                "schedule meeting at 7:00 PM on July 1, 2025",
                "schedule meeting on July 1st at 7 PM",
                "schedule meeting at 7pm on 1st of July 2025"
            ]
        }

    if start_time < datetime.now():
        try:
            start_time = start_time.replace(year=start_time.year + 1)
        except ValueError:
            # handle February 29th on non-leap years
            start_time = start_time + timedelta(days=365)


    end_time = start_time + timedelta(hours=1)
    
    print(f"[DEBUG] Parsed time: {start_time} to {end_time}")
    
    # Determine meeting title from query
    meeting_title = "Business Meeting"
    if "sales" in query.lower():
        meeting_title = "Sales Meeting"
    elif "finance" in query.lower() or "financial" in query.lower():
        meeting_title = "Financial Meeting"
    elif "review" in query.lower():
        meeting_title = "Review Meeting"
    
    # Convert datetime objects to ISO format strings for the Google Calendar API
    start_iso = start_time.isoformat() + "Z"
    end_iso = end_time.isoformat() + "Z"
    
    print(f"[DEBUG] Creating event: {meeting_title} from {start_iso} to {end_iso}")

    recurrence = None
    q_lower = query.lower()
    if "daily" in q_lower or "every day" in q_lower:
        recurrence = "RRULE:FREQ=DAILY"
    elif "weekly" in q_lower or "every week" in q_lower:
        recurrence = "RRULE:FREQ=WEEKLY"
    elif "monthly" in q_lower or "every month" in q_lower:
        recurrence = "RRULE:FREQ=MONTHLY"

    if "recurrence" in create_event.__code__.co_varnames:
        return create_event(
            meeting_title, start_iso, end_iso, recurrence=recurrence
        )
    else:
        return create_event(meeting_title, start_iso, end_iso)
# 🔹 FIXED: Combined workflow tool
def combined_analytics_and_email_calendar(query: str) -> dict:
    """Handle combined analytics + email + calendar workflows."""
    print(f"[DEBUG] Combined workflow called with: {query}")
    
    results = {}
    
    # First prepare for analytics capture
    prep_result = get_analytics_and_store(query)
    results["analytics_prep"] = prep_result
    
    # Note: Actual analytics delegation will happen via normal agent workflow
    # The agent should call format_and_store_agent_response() after delegation
    
    # Check for email request
    email_match = re.search(r"([\w.+-]+@[\w.-]+\.\w+)", query)
    if email_match:
        email_result = smart_send_email(query)
        results["email"] = email_result
    
    # Check for calendar request
    if any(k in query.lower() for k in ["schedule", "meeting", "event", "calendar"]):
        calendar_result = smart_schedule_event(query)
        results["calendar"] = calendar_result
    
    return results

# 🔹 FIXED: Root Agent with corrected syntax and tools
# ...existing code above remains the same...

root_agent = Agent(
    name="manager",
    model="gemini-2.0-flash", 
    description="Manager Orchestrator with multi-agent delegation + Gmail + Calendar tools",
    instruction="""
You are the **Manager Orchestrator Agent**.  
You are responsible for:
✅ Delegating queries to the correct sub-agents  
✅ Handling multi-domain analytics  
✅ Sending emails via Gmail (using smart_send_email)  
✅ Scheduling meetings in Google Calendar (using smart_schedule_event)  

---

🚨 **ANALYTICS HANDLING:**
For ANY analytics queries, follow this TWO-STEP process:
1. FIRST: Call `get_analytics_and_store(query)` to prepare for result capture
2. THEN: Delegate to appropriate sub-agent OR use cross-agent orchestrator
3. AFTER delegation: Call `format_and_store_agent_response(response)` with the agent's response

- Sales-related queries → `get_analytics_and_store(query)` THEN delegate to `sales_agent` THEN `format_and_store_agent_response(response)`
- Financial queries → `get_analytics_and_store(query)` THEN delegate to `financial_agent` THEN `format_and_store_agent_response(response)`
- Inventory queries → `get_analytics_and_store(query)` THEN delegate to `inventory_agent` THEN `format_and_store_agent_response(response)`
- Purchase queries → `get_analytics_and_store(query)` THEN delegate to `purchase_agent` THEN `format_and_store_agent_response(response)`
- Greetings or onboarding → Delegate to `greeting_agent`

✅ Example:
- "Give me the sales summary" → 
  1. `get_analytics_and_store("Give me the sales summary")`
  2. Delegate to `sales_agent`
  3. `format_and_store_agent_response(sales_agent_response)`

🔥 **CRITICAL:** ALWAYS call `format_and_store_agent_response()` after getting a response from analytics sub-agents.
This ensures results are properly formatted and captured for future email use.

---

🚨 **CROSS-AGENT ANALYTICS:**
If a query spans multiple domains (e.g., sales + inventory), call:
→ `handle_query_with_memory(query)`

✅ Example:
- "Compare sales and inventory trends" → `handle_query_with_memory("Compare sales and inventory trends")`

---

🚨 **EMAIL HANDLING (via Gmail API):**
If the query contains:
- Keywords like “send”, “email”, “mail”, “forward”
- OR includes an email address (e.g., user@example.com)

→ Call: `smart_send_email(query)`

✅ Example:
- "Send this to abhisheklgowda05@gmail.com" → `smart_send_email("Send this to abhisheklgowda05@gmail.com")`

🛡️ **If a sub-agent fails to send the email** (says it doesn’t have email functionality),  
→ Route the request back to **yourself** (Manager Agent) and reattempt `smart_send_email`.

---

🚨 **CALENDAR HANDLING (via Calendar API):**
If the query includes:
- "schedule", "meeting", "event", "calendar"

→ Call: `smart_schedule_event(query)`

✅ Example:
- "Schedule a meeting on July 1st at 7:00 PM" → `smart_schedule_event("Schedule a meeting on July 1st at 7:00 PM")`

---

🚨 **COMBINED WORKFLOW:**
If the query involves both analytics + calendar/email:
→ Call `combined_analytics_and_email_calendar(query)`

✅ Example:
- "Get sales report and mail it to CEO" → `combined_analytics_and_email_calendar("Get sales report and mail it to CEO")`

---

📌 **MANDATORY BEHAVIOR:**
if you are asked to send a mail and you are unable to access a suitable tool delegate back to the manager agent and try accessing the smart_send_email tool.
1. ALWAYS delegate domain-specific queries to the correct agent.
2. NEVER say "I cannot send emails" or "I cannot schedule meetings."
3. ALWAYS use tools (`smart_send_email`, `smart_schedule_event`, etc.) when triggers are detected.
4. If another agent fails due to missing Gmail/Calendar capability → You must take over.
5. ALWAYS return meaningful outputs. NEVER respond with just “OK.”

---

📌 **DEMONSTRATION SCENARIOS:**

✔️ "Get the sales summary" → 
  1. `get_analytics_and_store("Get the sales summary")`
  2. Delegate to `sales_agent`
  3. `format_and_store_agent_response(sales_response)`

✔️ "Email this summary to abhisheklgowda05@gmail.com" → `smart_send_email("Email this summary to abhisheklgowda05@gmail.com")`

✔️ "Schedule a product review meeting tomorrow at 3 PM" → `smart_schedule_event("Schedule a product review meeting tomorrow at 3 PM")`

✔️ "Get profit data and send it to finance@example.com" → `combined_analytics_and_email_calendar("Get profit data and send it to finance@example.com")`

"""
,
    tools=[
        FunctionTool(get_analytics_and_store),
        FunctionTool(format_and_store_agent_response),
        FunctionTool(handle_query_with_memory),
        FunctionTool(smart_send_email),
        FunctionTool(smart_schedule_event),
        FunctionTool(combined_analytics_and_email_calendar),
    ],
    sub_agents=[greeting_agent, sales_agent, purchase_agent, inventory_agent, financial_agent],
)
