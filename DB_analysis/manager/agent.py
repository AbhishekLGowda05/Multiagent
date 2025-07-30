import os
from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from manager.cross_agent_orchestrator import CrossAgentOrchestrator, DEFAULT_SPECS

from manager.sub_agents.sales_agent.agent import sales_agent
from manager.sub_agents.greeting_agent.agent import greeting_agent
from manager.sub_agents.purchase_agent.agent import purchase_agent
from manager.sub_agents.inventory_agent.agent import inventory_agent
from manager.sub_agents.financial_agent.agent import financial_agent

# Import Google utilities
from google_utils.gmail_tools import send_email
from google_utils.calendar_tools import create_event
import re
from datetime import datetime, timedelta
from typing import Any

# Initialize cross-agent orchestrator
cross_orchestrator = CrossAgentOrchestrator(DEFAULT_SPECS)

# Enhanced Google integration tools
def smart_send_email(query: str) -> Any:
    """Enhanced email tool that can handle business analytics context."""
    # Pattern 1: "Send email to [name] about [subject]"
    pattern1 = re.search(r"send (?:an )?email to (\w+)(?:@[\w.]+)? about (.+)", query, re.I)
    # Pattern 2: "Email [name] the [report type] results"
    pattern2 = re.search(r"email (\w+) the (.+?) results?", query, re.I)
    # Pattern 3: "Send [report] to [name]"
    pattern3 = re.search(r"send (.+?) (?:report |analysis )?to (\w+)", query, re.I)
    
    if pattern1:
        to_name, subject = pattern1.groups()
        to_email = f"{to_name.lower()}@example.com"
        body = f"Hi {to_name},\n\nRegarding: {subject}\n\nPlease find the requested information attached or let me know if you need additional details.\n\nBest regards"
        return send_email(to_email, subject, body)
    
    elif pattern2:
        to_name, report_type = pattern2.groups()
        to_email = f"{to_name.lower()}@example.com"
        subject = f"{report_type.title()} Analysis Results"
        body = f"Hi {to_name},\n\nPlease find the {report_type} analysis results as requested.\n\nBest regards"
        return send_email(to_email, subject, body)
    
    elif pattern3:
        report_type, to_name = pattern3.groups()
        to_email = f"{to_name.lower()}@example.com"
        subject = f"{report_type.title()} Report"
        body = f"Hi {to_name},\n\nAttached is the {report_type} report you requested.\n\nBest regards"
        return send_email(to_email, subject, body)
    
    else:
        raise ValueError("Could not parse email command. Please use format: 'Send email to [name] about [subject]'")

def smart_schedule_event(query: str) -> Any:
    """Enhanced calendar tool for business meetings and analytics sessions."""
    # Pattern 1: "Schedule [meeting] for [day] at [time]"
    pattern1 = re.search(r"schedule (.+?) (?:for |on )(today|tomorrow|monday|tuesday|wednesday|thursday|friday) (?:at |from )(\d+)(?::(\d+))?\s*(am|pm)(?:\s*to\s*(\d+)(?::(\d+))?\s*(am|pm))?", query, re.I)
    # Pattern 2: "Create meeting [subject] tomorrow from [time] to [time]"
    pattern2 = re.search(r"create (?:meeting |event )?(.+?) (today|tomorrow) from (\d+)\s*(am|pm) to (\d+)\s*(am|pm)", query, re.I)
    # Pattern 3: "Book [meeting type] session [when]"
    pattern3 = re.search(r"book (.+?) session (today|tomorrow)", query, re.I)
    
    base_date = datetime.now()
    
    if pattern1:
        meeting_type, day, start_hour, start_min, start_period, end_hour, end_min, end_period = pattern1.groups()
        
        # Calculate date
        if day.lower() == "tomorrow":
            base_date += timedelta(days=1)
        elif day.lower() == "today":
            pass  # Use current date
        
        # Parse start time
        start_hour = int(start_hour)
        if start_period.lower() == "pm" and start_hour != 12:
            start_hour += 12
        elif start_period.lower() == "am" and start_hour == 12:
            start_hour = 0
        
        start_time = base_date.replace(hour=start_hour, minute=int(start_min or 0), second=0, microsecond=0)
        
        # Parse end time (default to 1 hour later if not specified)
        if end_hour:
            end_hour = int(end_hour)
            if end_period.lower() == "pm" and end_hour != 12:
                end_hour += 12
            elif end_period.lower() == "am" and end_hour == 12:
                end_hour = 0
            end_time = base_date.replace(hour=end_hour, minute=int(end_min or 0), second=0, microsecond=0)
        else:
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
    
    elif pattern3:
        session_type, day = pattern3.groups()
        
        if day.lower() == "tomorrow":
            base_date += timedelta(days=1)
        
        # Default to 2 PM - 3 PM for sessions
        start_time = base_date.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        return create_event(f"{session_type.title()} Session", start_time.isoformat() + "Z", end_time.isoformat() + "Z")
    
    else:
        raise ValueError("Could not parse calendar command. Please use format: 'Schedule [meeting] for [day] at [time]'")

def combined_analytics_and_email(query: str) -> Any:
    """Handle queries that combine analytics and email sending."""
    # Extract the analytics part and email part
    if "and email" in query.lower() or "then send" in query.lower():
        parts = re.split(r"(?:and|then)\s*(?:email|send)", query, flags=re.I)
        if len(parts) == 2:
            analytics_query = parts[0].strip()
            email_query = "send" + parts[1].strip()
            
            # First get analytics results
            analytics_result = cross_orchestrator.handle_query(analytics_query)
            
            # Then send email
            email_result = smart_send_email(email_query)
            
            return {
                "analytics_result": analytics_result,
                "email_result": email_result,
                "message": "Analytics completed and email sent successfully"
            }
    
    raise ValueError("Could not parse combined analytics and email command")

root_agent = Agent(
    name="manager",
    model="gemini-2.0-flash",
    description="Central orchestrator for analytics requests with Google integration",
    instruction="""
    You are the intelligent Manager Orchestrator for a comprehensive multi-agent analytics system powered by Gemini 2.0 Flash.

🎯 Your responsibilities:
1. Analyze user queries.
2. Identify the analysis type (descriptive, diagnostic, predictive, prescriptive).
3. Detect relevant business domains and select appropriate agents.
4. Orchestrate single-agent or cross-agent workflows.
5. Integrate communication and scheduling via Gmail and Google Calendar tools.

---

## 📌 DOMAIN DETECTION
Identify which domain(s) the query touches:
- Sales: sales, revenue, customers, invoices
- Purchase: purchase, suppliers, vendors, procurement
- Inventory: inventory, stock, items, products
- Financial: profit, cash flow, balance, accounting

---

## 📌 CROSS-AGENT RULES
Some queries require multiple agents for complete insights:

1. **Business Overview**
   - Agents: sales_agent + purchase_agent + inventory_agent + financial_agent
   - Keywords: "business performance", "overall status", "comprehensive analysis"

2. **Profitability Analysis**
   - Agents: sales_agent + financial_agent
   - Keywords: "profit vs sales", "sales margins", "revenue profitability"

3. **Operational Efficiency**
   - Agents: inventory_agent + purchase_agent + sales_agent
   - Keywords: "efficiency analysis", "turnover", "operational performance"

4. **Cost vs Revenue**
   - Agents: sales_agent + purchase_agent + financial_agent
   - Keywords: "revenue vs costs", "expenses vs sales", "profit analysis"

5. **Inventory Planning**
   - Agents: inventory_agent + sales_agent
   - Keywords: "inventory forecasting", "demand planning", "stock requirements"

---

## 📌 GOOGLE WORKSPACE INTEGRATION
Detect and handle queries involving email or calendar actions:

- Email keywords: "send email", "email", "mail", "share report"
- Calendar keywords: "schedule", "create meeting", "add to calendar", "book event"

**Combined Workflow Examples:**
- "Analyze quarterly performance and email the results to CFO"
- "Get profit analysis and schedule a review meeting tomorrow at 10 AM"
- "Generate sales report and send it to the team"

When detected:
1. Perform analytics first (single or cross-agent).
2. Pass results to email or calendar tool as needed.
3. Confirm completion in the response.

---

## 📌 EXECUTION RULES

### 🔹 Single Domain Query → Single Agent
- Only one domain detected → Delegate to that agent.

### 🔹 Multi-Domain Query → Cross-Agent
- Multiple domains or comparative language detected ("vs", "compare", "impact") → Call all relevant agents and merge outputs.

### 🔹 Google Actions
- Email-only request → Call Gmail tool.
- Calendar-only request → Call Calendar tool.
- Combined analytics + Google action → Perform analytics → Send via email or schedule event.

---

## 📌 RESPONSE FORMAT
When combining multiple agents or Google actions, structure output like this:

📊 **Sales Analysis (sales_agent)**: [findings]  
💰 **Financial Analysis (financial_agent)**: [findings]  
📦 **Inventory Analysis (inventory_agent)**: [findings]  
🛒 **Purchase Analysis (purchase_agent)**: [findings]  

🔍 **Cross-Domain Insight**: [merged conclusion]  
✅ **Action Taken**: [email sent / event scheduled with link]

---

## 📌 ERROR HANDLING
- If unsure which agents to call, ask clarifying questions.
- If one agent fails, continue with others and note the missing piece.
- Always explain which agents and tools were used.

---

## 📌 PURPOSE
Your goal is to act as a business assistant:
- Deliver descriptive, diagnostic, predictive, and prescriptive insights.
- Seamlessly integrate analytics with communication and scheduling.
- Provide complete, actionable business workflows in a single conversation.
""",
    tools=[
        cross_orchestrator.handle_query,
        FunctionTool(smart_send_email, name="smart_send_email"),
        FunctionTool(smart_schedule_event, name="smart_schedule_event"), 
        FunctionTool(combined_analytics_and_email, name="combined_analytics_and_email"),
    ],
    sub_agents=[
        greeting_agent,
        sales_agent,
        purchase_agent,
        inventory_agent,
        financial_agent,
    ],
)