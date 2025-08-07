from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
import os, sys, re, json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Any

try:
    import dateparser  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    dateparser = None

# ✅ Add Int-Assignment root path so google_utils is discoverable
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))  # Goes up to📌 **MANDATORY BEHAVIOR:**

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ✅ Import Google utilities (now will work inside ADK)
from google_utils.gmail_tools import send_email, read_emails, delete_email

from google_utils.calendar_tools import (
    create_event,
     create_recurring_event,
     build_daily_rrule,
     build_interval_rrule,
)


# Chart generation utility
# from visualization_utils import generate_chart  # Comment out to use local version

# ✅ Import sub-agents (fixed import paths)
from .sub_agents.sales_agent.agent import sales_agent
from .sub_agents.greeting_agent.agent import greeting_agent
from .sub_agents.purchase_agent.agent import purchase_agent
from .sub_agents.inventory_agent.agent import inventory_agent
from .sub_agents.financial_agent.agent import financial_agent

# ✅ Cross-agent orchestrator
from .cross_agent_orchestrator import CrossAgentOrchestrator, DEFAULT_SPECS
cross_orchestrator = CrossAgentOrchestrator(DEFAULT_SPECS)

# ✅ Memory for last analytics result
LAST_ANALYTICS_RESULT: str = ""
LAST_ANALYTICS_DATA: dict = {}

# Utility helpers for enhanced email output
def generate_chart(analytics_data: dict = None, path: str = "chart.png") -> str:
    """Create a chart from analytics data and return the file path."""
    import matplotlib.pyplot as plt
    
    # If analytics_data is provided, create charts based on the data
    if analytics_data and isinstance(analytics_data, dict):
        if "top_customers" in analytics_data:
            # Create bar chart for top customers
            customers = list(analytics_data["top_customers"].keys())
            invoice_counts = list(analytics_data["top_customers"].values())
            
            plt.figure(figsize=(12, 8))
            bars = plt.bar(customers, invoice_counts, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
            plt.title("Top Customers by Invoice Count", fontsize=16, fontweight='bold')
            plt.xlabel("Customers")
            plt.ylabel("Number of Invoices")
            plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close()
            
        elif "financial_summary" in analytics_data:
            # Create financial chart
            categories = list(analytics_data["financial_summary"].keys())
            amounts = list(analytics_data["financial_summary"].values())
            
            plt.figure(figsize=(10, 6))
            plt.bar(categories, amounts, color=['green', 'red', 'blue'])
            plt.title("Financial Summary", fontsize=16, fontweight='bold')
            plt.ylabel("Amount ($)")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close()
            
        elif "inventory_levels" in analytics_data:
            # Create inventory chart
            items = list(analytics_data["inventory_levels"].keys())
            stock = list(analytics_data["inventory_levels"].values())
            
            plt.figure(figsize=(10, 6))
            plt.bar(items, stock, color='skyblue')
            plt.title("Current Inventory Levels", fontsize=16, fontweight='bold')
            plt.xlabel("Items")
            plt.ylabel("Stock Level")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close()
            
        else:
            # Generic chart for other data types
            keys = list(analytics_data.keys())[:5]  # Limit to 5 items
            values = [analytics_data[k] for k in keys if isinstance(analytics_data[k], (int, float))]
            
            if values:
                plt.figure(figsize=(10, 6))
                plt.bar(keys[:len(values)], values, color='lightcoral')
                plt.title("Analytics Data", fontsize=16, fontweight='bold')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(path, dpi=300, bbox_inches='tight')
                plt.close()
            else:
                # Fallback to default chart
                values = [1, 2, 3, 4]
                plt.figure()
                plt.plot(range(1, len(values) + 1), values, marker="o")
                plt.title("Analytics Chart")
                plt.xlabel("Index")
                plt.ylabel("Value")
                plt.tight_layout()
                plt.savefig(path)
                plt.close()
    else:
        # Default chart when no analytics data
        values = [1, 2, 3, 4]
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


# 🔹 NEW: Universal analytics detection and capture hook
def auto_detect_and_capture_analytics(response: str, query: str = "") -> str:
    """
    Universal hook to detect analytics responses and automatically capture them.
    This ensures LAST_ANALYTICS_RESULT is always populated when analytics data is present.
    """
    print(f"[DEBUG] ===== AUTO-DETECTION HOOK CALLED =====")
    print(f"[DEBUG] Response type: {type(response)}")
    print(f"[DEBUG] Response length: {len(str(response))}")
    print(f"[DEBUG] Response preview: {str(response)[:300]}...")
    
    response_str = str(response).lower()
    
    # Detect if this is an analytics response by checking for key indicators
    analytics_indicators = [
        # Sales indicators
        "top customers", "customer", "invoice", "sales", "voucher", "revenue",
        # Financial indicators  
        "profit", "loss", "expense", "financial", "income", "balance",
        # Inventory indicators
        "inventory", "stock", "item", "product", "quantity",
        # Purchase indicators
        "purchase", "vendor", "supplier", "procurement", "order",
        # General business indicators
        "total", "amount", "count", "summary", "report", "analysis"
    ]
    
    # Check if response contains analytics data
    contains_analytics = any(indicator in response_str for indicator in analytics_indicators)
    
    # Also check if response contains structured data patterns
    has_data_patterns = bool(
        re.search(r"\d+\s*(invoices?|customers?|items?|orders?)", response_str) or
        re.search(r"\$\d+", response_str) or
        re.search(r"\d+\s*-\s*\w+", response_str) or
        re.search(r"total.*:\s*\d+", response_str)
    )
    
    print(f"[DEBUG] Contains analytics indicators: {contains_analytics}")
    print(f"[DEBUG] Has data patterns: {has_data_patterns}")
    
    if contains_analytics or has_data_patterns:
        print(f"[DEBUG] 🎯 ANALYTICS DETECTED - Auto-capturing response")
        
        # Auto-format and store the response
        formatted_response = format_and_store_agent_response(str(response))
        
        print(f"[DEBUG] ✅ Analytics auto-capture completed")
        return response
    else:
        print(f"[DEBUG] ❌ No analytics detected - skipping auto-capture")
        return response

# 🔹 ENHANCED: Format agent response with improved regex patterns and analytics capture
def format_and_store_agent_response(response: str) -> str:
    """Format agent response and store it for email use with robust data extraction."""
    print(f"[DEBUG] ===== FORMATTING AGENT RESPONSE =====")
    print(f"[DEBUG] Response type: {type(response)}")
    print(f"[DEBUG] Response length: {len(str(response))}")
    print(f"[DEBUG] Response preview: {str(response)[:300]}...")
    
    # Parse analytics data from response for chart generation
    analytics_data = {}
    response_str = str(response)
    
    # Extract top customers data with flexible regex patterns
    if "customer" in response_str.lower() or "invoice" in response_str.lower():
        # Enhanced pattern to match multiple formats:
        # "BUDHAL CELL WORLD (25 invoices)", "RAVI ELECTRONICS: 10", "SAHANA CELLULAR - 9"
        customer_pattern = r"([A-Za-z0-9\s&]+)[(:|-]\s*(\d+)(?:\s*invoices?)?"
        matches = re.findall(customer_pattern, response_str)
        
        if matches:
            top_customers = {}
            for customer, count in matches:
                customer_clean = customer.strip()
                if customer_clean and len(customer_clean) > 2:
                    top_customers[customer_clean] = int(count)
            
            if top_customers:
                analytics_data["top_customers"] = top_customers
                print(f"[DEBUG] Extracted top customers: {top_customers}")
        
        # If no structured data found but response contains customer info, create generic data
        if not analytics_data and any(word in response_str.lower() for word in ["customer", "invoice", "sales"]):
            # Extract any numbers from the response to create meaningful chart data
            numbers = re.findall(r'\d+', response_str)
            if len(numbers) >= 3:
                analytics_data["top_customers"] = {
                    f"Customer {i+1}": int(numbers[i]) for i in range(min(5, len(numbers)))
                }
                print(f"[DEBUG] Created generic customer data from numbers: {analytics_data}")
    
    # Extract financial data with enhanced patterns
    if any(word in response_str.lower() for word in ["revenue", "profit", "expense", "income", "financial"]):
        # Enhanced financial pattern: "Revenue: $1000", "Profit - 500", "Expenses (200)"
        financial_pattern = r"(revenue|profit|expense|income|sales)[:\-\(]\s*\$?(\d+(?:,\d+)*(?:\.\d+)?)"
        matches = re.findall(financial_pattern, response_str, re.IGNORECASE)
        if matches:
            financial_summary = {}
            for category, amount in matches:
                financial_summary[category.title()] = float(amount.replace(',', ''))
            if financial_summary:
                analytics_data["financial_summary"] = financial_summary
                print(f"[DEBUG] Extracted financial data: {financial_summary}")
    
    # Extract inventory data with enhanced patterns
    if any(word in response_str.lower() for word in ["inventory", "stock", "item", "product"]):
        # Enhanced inventory pattern: "Product A: 50", "Item B - 25", "Stock C (10)"
        inventory_pattern = r"([A-Za-z0-9\s]+)[:\-\(]\s*(\d+)"
        matches = re.findall(inventory_pattern, response_str)
        if matches:
            inventory_levels = {}
            for item, level in matches:
                item_clean = item.strip()
                if item_clean and len(item_clean) > 2 and not item_clean.lower() in ['total', 'count', 'number']:
                    inventory_levels[item_clean] = int(level)
            if inventory_levels:
                analytics_data["inventory_levels"] = inventory_levels
                print(f"[DEBUG] Extracted inventory data: {inventory_levels}")
    
    # If no specific data extracted but response contains analytics keywords, create generic data
    if not analytics_data:
        analytics_keywords = ["total", "count", "amount", "summary", "report", "analysis"]
        if any(keyword in response_str.lower() for keyword in analytics_keywords):
            # Extract numbers to create a meaningful chart
            numbers = re.findall(r'\d+', response_str)
            if numbers:
                analytics_data["general_metrics"] = {
                    f"Metric {i+1}": int(numbers[i]) for i in range(min(4, len(numbers)))
                }
                print(f"[DEBUG] Created general analytics data: {analytics_data}")
    
    # Determine report type from the response content
    if any(word in response_str.lower() for word in ["sales", "invoice", "customer", "voucher"]):
        report_type = "SALES SUMMARY"
        emoji = "📊"
    elif any(word in response_str.lower() for word in ["financial", "profit", "revenue", "expense"]):
        report_type = "FINANCIAL ANALYSIS"
        emoji = "💰"
    elif any(word in response_str.lower() for word in ["inventory", "stock", "item"]):
        report_type = "INVENTORY ANALYSIS"
        emoji = "📦"
    elif any(word in response_str.lower() for word in ["purchase", "vendor", "supplier"]):
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
    
    # Store both the formatted result and analytics data
    set_last_analytics_result(formatted_result)
    
    # Store analytics data globally for chart generation
    global LAST_ANALYTICS_DATA
    LAST_ANALYTICS_DATA = analytics_data
    print(f"[DEBUG] Stored analytics data: {analytics_data}")
    
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

# 🔹 SIMPLIFIED: Analytics capture function that hooks into responses
def capture_analytics_after_response(query: str, response: str) -> str:
    """
    Simple function to capture analytics after getting a response from any agent.
    This ensures LAST_ANALYTICS_RESULT is always populated for email functionality.
    """
    print(f"[DEBUG] ===== ANALYTICS CAPTURE HOOK =====")
    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] Response preview: {str(response)[:200]}...")
    
    # Always call format_and_store for analytics queries
    query_lower = query.lower()
    is_analytics = any(keyword in query_lower for keyword in [
        "sales", "customer", "invoice", "revenue", "financial", "profit", 
        "inventory", "stock", "purchase", "vendor", "summary", "report"
    ])
    
    if is_analytics:
        print(f"[DEBUG] 🎯 Analytics query detected - capturing response")
        format_and_store_agent_response(response)
        print(f"[DEBUG] ✅ Analytics captured successfully")
    else:
        print(f"[DEBUG] Non-analytics query - skipping capture")
    
    print(f"[DEBUG] ===== CAPTURE HOOK COMPLETED =====")
    return response


# 🔹 NEW: Delegate queries and automatically store sub-agent responses
def delegate_with_capture(query: str) -> dict:
    """Delegate a query to sub-agents and store each response for email use."""
    # Use the cross-agent orchestrator to route the query
    responses = cross_orchestrator.handle_query(query)

    # Iterate through each agent's tool output and store the latest text
    for agent_name, agent_data in responses.items():
        if agent_name.startswith("_"):
            continue
        for tool_result in agent_data.values():
            format_and_store_agent_response(str(tool_result))

    return responses

# 🔹 FIXED: Email tool with proper pattern matching and enhanced debugging
# Replace the smart_send_email function with this simplified version:

def smart_send_email(query: str) -> dict:
    """Send email based on natural language query with memory of last analytics result."""
    print(f"[DEBUG] ===== EMAIL FUNCTION CALLED =====")
    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] LAST_ANALYTICS_RESULT length: {len(LAST_ANALYTICS_RESULT)}")
    print(f"[DEBUG] LAST_ANALYTICS_RESULT first 500 chars: {LAST_ANALYTICS_RESULT[:500]}")
    print(f"[DEBUG] LAST_ANALYTICS_RESULT type: {type(LAST_ANALYTICS_RESULT)}")
    
    # Pattern 1: "send this to email@domain.com" or "mail this to email@domain.com"
    pattern1 = re.search(r"(?:send|mail) (?:this|these|mail|email) to ([\w.+-@\s,]+)", query, re.I)

    # Pattern 2: "send email to email@domain.com"
    pattern2 = re.search(r"send (?:an )?email to ([\w.+-@\s,]+)", query, re.I)

    # Pattern 3: Just find any email address in the query
    pattern3 = re.search(r"([\w.+-]+@[\w.-]+\.\w+)", query, re.I)

    email_text = None
    if pattern1:
        email_text = pattern1.group(1)
        subject = "Business Analysis Results"
        print(f"[DEBUG] Pattern 1 matched - Email text: {email_text}")
    elif pattern2:
        email_text = pattern2.group(1)
        subject = "Business Report"
        print(f"[DEBUG] Pattern 2 matched - Email text: {email_text}")
    elif pattern3:
        email_text = query
        subject = "Analytics Report"
        print(f"[DEBUG] Pattern 3 matched - Using entire query")
    else:
        print(f"[DEBUG] No email pattern matched")
        return {"status": "error", "message": "No email address found in query"}

    # Extract all email addresses, allowing comma or whitespace separation
    email_pattern = r"[\w.+-]+@[\w.-]+\.\w+"
    recipients = re.findall(email_pattern, email_text)
    print(f"[DEBUG] Extracted {len(recipients)} recipient(s): {recipients}")

    if not recipients:
        return {"status": "error", "message": "No valid email addresses found"}
    
    # 🚨 FAIL-SAFE CHECK: Ensure we have analytics data before sending
    if not LAST_ANALYTICS_RESULT or len(LAST_ANALYTICS_RESULT.strip()) == 0:
        error_msg = """❌ No analytics data captured!
        
To send a meaningful email with charts and data:
1. First run an analytics query (e.g., "get sales summary", "show top customers")
2. Then request the email again

Currently no analytics data is stored in memory."""
        
        print(f"[ERROR] {error_msg}")
        return {
            "status": "error", 
            "message": error_msg,
            "suggestion": "Please run an analytics query first, then retry the email request"
        }
    
    # Use the stored analytics result
    body_text = LAST_ANALYTICS_RESULT
    print(f"[DEBUG] Using stored analytics result, length: {len(body_text)}")

    # Generate chart for visual enhancement using real analytics data
    global LAST_ANALYTICS_DATA
    
    # 🚨 FAIL-SAFE CHECK: Ensure we have chart data
    if not LAST_ANALYTICS_DATA or len(LAST_ANALYTICS_DATA) == 0:
        print(f"[WARNING] No analytics data for charts - using fallback message")
        # Don't send blank email - inform user about the issue
        return {
            "status": "error",
            "message": "Analytics data was captured but chart data is missing. Please retry the analytics query and email request.",
            "captured_text": body_text[:200] + "..." if len(body_text) > 200 else body_text
        }
    
    chart_file = generate_chart(LAST_ANALYTICS_DATA, path="analytics_chart.png")
    attach_pdf = "pdf" in query.lower()

    # Create enhanced HTML email body with embedded chart
    html_body = f"""<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.6;
        }}
        .header {{
            background-color: #f4f4f4;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .content {{
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 10px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }}
        pre {{
            white-space: pre-wrap;
            font-family: monospace;
            line-height: 1.4;
            background-color: #f8f8f8;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #333; margin: 0;">{subject}</h2>
    </div>
    
    <div class="content">
        <pre>{body_text}</pre>
    </div>
    
    <div class="chart-container">
        <h3 style="color: #555;">📊 Visual Analysis</h3>
        <img src='cid:chart' alt="Analytics Chart" style="max-width: 100%; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    </div>
    
    <div class="footer">
        Generated by Business Analytics System<br>
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>"""

    attachments = [chart_file]
    if attach_pdf:
        pdf_path = _create_pdf(body_text, chart_file)
        attachments.append(pdf_path)

    print(f"[DEBUG] Final email body length: {len(html_body)}")
    print(f"[DEBUG] Final email body preview: {html_body[:200]}...")
    print(f"[DEBUG] Sending email with {len(attachments)} attachment(s)...")
    print(f"[SUCCESS] Email contains real analytics data: {len(LAST_ANALYTICS_DATA)} data points")

    results = []
    for to_email in recipients:
        try:
            print(f"[DEBUG] Sending to {to_email}")
            result = _send_email_html(to_email, subject, html_body, attachments)
            results.append({"email": to_email, "result": result})
            print(f"[SUCCESS] Email sent to {to_email}")
        except Exception as e:
            print(f"[ERROR] Email sending failed for {to_email}: {str(e)}")
            results.append({"email": to_email, "error": str(e)})

    print(f"[DEBUG] ===== EMAIL FUNCTION COMPLETED =====")
    return {"status": "success", "recipients": recipients, "results": results}

# 🔹 Schedule a meeting in Google Calendar
def smart_schedule_event(query: str) -> dict:
    """Schedule a calendar event based on a natural language query."""
    print(f"[DEBUG] ===== CALENDAR FUNCTION CALLED =====")
    print(f"[DEBUG] Query: {query}")

    # Try to parse a start time from the query
    start_time = None
    if dateparser:
        try:
            start_time = dateparser.parse(query, settings={"PREFER_DATES_FROM": "future"})
        except Exception:
            start_time = None

    if start_time is None:
        start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)

    # Basic title extraction
    title_match = re.search(r"(?:schedule|create|add)\s+(?:a\s+|an\s+)?(.+?)(?:\s+on|\s+at|$)", query, re.I)
    title = title_match.group(1).strip() if title_match else "Meeting"

    try:
        event = create_event(title, start_time, end_time, description=query)
        print(f"[DEBUG] Event created: {event}")
        return {"status": "success", "event": event}
    except Exception as e:
        print(f"[ERROR] Failed to schedule event: {e}")
        return {"status": "error", "message": str(e)}

# 🔹 NEW: Read recent emails from Gmail inbox
def smart_read_last_emails(count: int = 3) -> list[dict[str, str]]:
    """Return the subject and snippet of the last `count` inbox emails."""
    try:
        # Attempt to use maxResults if supported
        messages = read_emails(query="label:inbox", maxResults=count)
    except TypeError:
        # Fallback for older versions without maxResults
        messages = read_emails("label:inbox")[:count]

    results: list[dict[str, str]] = []

    # Mock mode or missing credentials – return placeholder data
    if os.getenv("MOCK_GOOGLE_APIS") == "true":
        for i in range(min(count, len(messages))):
            results.append(
                {
                    "subject": f"Mock email {i + 1}",
                    "snippet": "This is a mock email snippet",
                }
            )
        return results

    try:
        from googleapiclient.discovery import build
        from google_utils.auth import get_credentials

        creds = get_credentials(["https://www.googleapis.com/auth/gmail.readonly"])
        service = build("gmail", "v1", credentials=creds)

        for msg in messages[:count]:
            detail = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="full")
                .execute()
            )
            headers = detail.get("payload", {}).get("headers", [])
            subject = next(
                (h.get("value", "") for h in headers if h.get("name") == "Subject"),
                "",
            )
            snippet = detail.get("snippet", "")
            results.append({"subject": subject, "snippet": snippet})
    except Exception as e:
        print(f"[ERROR] smart_read_last_emails failed: {e}")

    return results

# 🔹 Delete the last sent email

def smart_delete_last_email() -> dict:
    """Delete the most recent sent email by moving it to trash."""
    print(f"[DEBUG] ===== DELETE LAST EMAIL CALLED =====")
    try:
        messages = read_emails(query="label:sent", maxResults=1)
        if not messages:
            print(f"[DEBUG] No sent emails found")
            return {"status": "error", "message": "No sent emails found"}

        message_id = messages[0].get("id")
        delete_email(message_id)
        print(f"[DEBUG] Deleted email id: {message_id}")
        return {"status": "success", "message": f"Deleted email id: {message_id}"}
    except Exception as e:
        print(f"[ERROR] Failed to delete email: {e}")
        return {"status": "error", "message": f"Failed to delete email: {e}"}

# 🔹 ROOT AGENT DEFINITION

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
✅ Deleting the last sent email (using smart_delete_last_email)


---

🚨 **CRITICAL ANALYTICS WORKFLOW:**  
For ANY analytics query, you MUST follow this exact process:

1️⃣ **ALWAYS delegate to the appropriate sub-agent FIRST**
   → Use `delegate_with_capture(query)` to auto-store responses
2️⃣ **IMMEDIATELY after getting the response**, call `capture_analytics_after_response(query, response)`
3️⃣ This ensures analytics data is captured for email functionality

🔹 **Analytics Queries** (sales, financial, inventory, purchase):
   → Delegate to appropriate agent → `capture_analytics_after_response(query, response)`



🔹 **Delete Email Queries** (delete last sent mail):
   → Call `smart_delete_last_email()`

🔹 **Calendar Queries** (schedule, meeting, event):
   → Call `smart_schedule_event(query)`

🔹 **Inbox Queries** (read, inbox, emails):
   → Call `smart_read_last_emails(count)` (defaults to 3)

🔹 **Greetings** (hello, hi):
   → Delegate to `greeting_agent` (no analytics capture needed)

---

🚨 **EMAIL HANDLING:**  
If the query contains:
- Keywords like "send", "email", "mail", "forward"
- OR includes an email address (e.g., user@example.com)

→ Call: `smart_send_email(query)`

This will automatically use the stored analytics data from previous queries.

If the user asks to delete the most recent sent email:

→ Call: `smart_delete_last_email()`

---

🚨 **CALENDAR HANDLING:**  
If the query includes:
- "schedule", "meeting", "event", "calendar"

→ Call: `smart_schedule_event(query)`

---

📌 **CRITICAL EXAMPLES:**  

✔️ User: "Get sales summary" 
   → Delegate to `sales_agent` 
   → `capture_analytics_after_response("Get sales summary", sales_response)`

✔️ User: "Send this to john@company.com"
   → `smart_send_email("Send this to john@company.com")`
   → (automatically uses previously captured analytics)

✔️ User: "Delete the last sent mail"
   → `smart_delete_last_email()`

✔️ User: "Hello"
   → Delegate to `greeting_agent` (no capture needed)

✔️ User: "Read my last 3 emails"
   → `smart_read_last_emails(count=3)`

---

� **MANDATORY RULES:**
1. **ALWAYS** call `capture_analytics_after_response()` after ANY analytics delegation
2. **NEVER** skip analytics capture for sales/financial/inventory/purchase queries  
3. Email function will FAIL if no analytics data was captured - this prevents blank emails
4. **ALWAYS** delegate to the correct sub-agent based on query domain
5. **NEVER** say "I cannot send emails" - use `smart_send_email()` tool

---

🎯 **FAIL-SAFE EMAIL BEHAVIOR:**
If user requests email but no analytics was captured, the email function will return an error asking them to run analytics first. This prevents sending blank emails with default charts.

"""
,

    tools=[
        FunctionTool(delegate_with_capture),
        FunctionTool(capture_analytics_after_response),
        FunctionTool(get_analytics_and_store),
        FunctionTool(format_and_store_agent_response),
        FunctionTool(smart_send_email),
        FunctionTool(smart_schedule_event),
        FunctionTool(smart_delete_last_email),

    ],
    sub_agents=[greeting_agent, sales_agent, purchase_agent, inventory_agent, financial_agent],
)
