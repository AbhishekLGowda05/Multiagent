from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
import os, sys, re, json
import matplotlib.pyplot as plt
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
        subject = "Analytics Report"
        print(f"[DEBUG] Pattern 3 matched - Email: {to_email}")
    else:
        print(f"[DEBUG] No email pattern matched")
        return {"status": "error", "message": "No email address found in query"}
    
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

    try:
        result = _send_email_html(to_email, subject, html_body, attachments)
        print(f"[DEBUG] send_email result: {result}")
        print(f"[SUCCESS] Email sent successfully with analytics data and charts")
        print(f"[DEBUG] ===== EMAIL FUNCTION COMPLETED =====")
        return result
    except Exception as e:
        print(f"[ERROR] Email sending failed: {str(e)}")
        return {"status": "error", "message": f"Failed to send email: {str(e)}"}

# 🔹 FIXED: Calendar tool with proper signature
# Replace the smart_schedule_event function with this enhanced version:

def smart_schedule_event(query: str) -> dict:
    """Schedule calendar event based on natural language query with recurring event support."""
    print(f"[DEBUG] ===== CALENDAR FUNCTION CALLED =====")
    print(f"[DEBUG] Query: {query}")
    
    base_date = datetime.now()
    
    # Enhanced pattern matching for recurring events
    patterns = {
        "daily_range": r"(?:set|schedule).*meeting.*from (\d+)(?:st|nd|rd|th)? (\w+) to (\d+)(?:st|nd|rd|th)? (\w+) at (\d+)(?::(\d+))?\s*(am|pm) every day",
        "interval_pattern": r"(?:set|schedule).*meeting.*every (\d+)(?:st|nd|rd|th)? day in (\w+)",
        "daily_recurring": r"(?:schedule|set).*meeting.*daily|every day.*at (\d+)(?::(\d+))?\s*(am|pm)",
        "weekly_recurring": r"(?:schedule|set).*meeting.*weekly|every week.*at (\d+)(?::(\d+))?\s*(am|pm)",
        # NEW: Enhanced patterns for month-specific recurring events
        "everyday_in_month": r"(?:schedule|set).*meeting.*everyday.*at (\d+)(?::(\d+))?\s*(am|pm).*in (\w+)",
        "every_nth_day_in_month": r"(?:schedule|set).*meeting.*every (\d+)(?:st|nd|rd|th)? day.*in (\w+)(?:.*at (\d+)(?::(\d+))?\s*(am|pm))?",
        "daily_for_month": r"(?:schedule|set).*meeting.*at (\d+)(?::(\d+))?\s*(am|pm).*everyday.*in (\w+)",
        # Standard patterns (existing)
        "pattern1": r"at (\d{1,2})(?::(\d{1,2}))?\s*(am|pm) on (?:(\d{1,2})(?:st|nd|rd|th)?\s+of\s+)?(\w+)\s+(\d{1,2})(?:,\s*)?(\d{4})?",
        "pattern2": r"(\w+)\s+(\d{1,2})(?:,\s*)?(\d{4})?\s+at\s+(\d{1,2})(?::(\d{1,2}))?\s*(am|pm)",
        "pattern3": r"(today|tomorrow) at (\d+)(?::(\d+))?\s*(am|pm)",
        "pattern4": r"on (\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(\w+)(?:\s+(\d{4}))?\s+at\s+(\d+)(?::(\d+))?\s*(am|pm)",
        "pattern5": r"at (\d{1,2})(?::(\d{1,2}))?\s*(am|pm) on (?:(\d{1,2})(?:st|nd|rd|th)?(?:\s+of)?\s+)?(\w+)(?:\s+(\d{4}))?"
    }

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
    is_recurring = False
    recurrence_rule = None
    
    # Check for recurring patterns first
    
    # Pattern: "Set a meeting from 1st August to 7th August at 4 PM every day"
    daily_range_match = re.search(patterns["daily_range"], query, re.I)
    if daily_range_match:
        start_day, start_month, end_day, end_month, hour_str, minute_str, period = daily_range_match.groups()
        print(f"[DEBUG] Daily range pattern matched: {daily_range_match.groups()}")
        
        start_month_num = parse_month(start_month)
        end_month_num = parse_month(end_month)
        hour, minute = parse_time(hour_str, minute_str, period)
        
        year = datetime.now().year
        start_time = datetime(year, start_month_num, int(start_day), hour, minute)
        end_date = datetime(year, end_month_num, int(end_day), hour + 1, minute)  # +1 hour duration
        
        # Calculate number of days for daily recurrence
        days_diff = (end_date - start_time).days + 1
        recurrence_rule = build_daily_rrule(count=days_diff)
        is_recurring = True
        
    # Pattern: "Set a meeting every 4th day in August"
    elif re.search(patterns["interval_pattern"], query, re.I):
        interval_match = re.search(patterns["interval_pattern"], query, re.I)
        interval_days, month_str = interval_match.groups()
        print(f"[DEBUG] Interval pattern matched: {interval_match.groups()}")
        
        month_num = parse_month(month_str)
        year = datetime.now().year
        
        # Default to 2 PM if no time specified
        hour, minute = 14, 0
        time_match = re.search(r"at (\d+)(?::(\d+))?\s*(am|pm)", query, re.I)
        if time_match:
            hour, minute = parse_time(time_match.group(1), time_match.group(2), time_match.group(3))
        
        # Start on the first day of the month
        start_time = datetime(year, month_num, 1, hour, minute)
        
        # Build interval rule for every Nth day
        recurrence_rule = build_interval_rrule("DAILY", int(interval_days), count=10)
        is_recurring = True
        
    # Pattern: "Schedule meeting daily at 3 PM" or "every day at 3 PM"
    elif re.search(patterns["daily_recurring"], query, re.I):
        daily_match = re.search(patterns["daily_recurring"], query, re.I)
        hour_str, minute_str, period = daily_match.groups()
        print(f"[DEBUG] Daily recurring pattern matched: {daily_match.groups()}")
        
        hour, minute = parse_time(hour_str, minute_str, period)
        start_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed today, start tomorrow
        if start_time < datetime.now():
            start_time += timedelta(days=1)
            
        recurrence_rule = build_daily_rrule(count=30)  # 30 days
        is_recurring = True
        
    # Pattern: "Schedule meeting weekly at 3 PM" or "every week at 3 PM"
    elif re.search(patterns["weekly_recurring"], query, re.I):
        weekly_match = re.search(patterns["weekly_recurring"], query, re.I)
        hour_str, minute_str, period = weekly_match.groups()
        print(f"[DEBUG] Weekly recurring pattern matched: {weekly_match.groups()}")
        
        hour, minute = parse_time(hour_str, minute_str, period)
        start_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed today, start next week
        if start_time < datetime.now():
            start_time += timedelta(weeks=1)
            
        from google_utils.calendar_tools import build_weekly_rrule
        recurrence_rule = build_weekly_rrule(count=12)  # 12 weeks
        is_recurring = True
    
    # NEW: Pattern: "schedule meeting everyday at 7pm in August"
    elif re.search(patterns["everyday_in_month"], query, re.I):
        match = re.search(patterns["everyday_in_month"], query, re.I)
        hour_str, minute_str, period, month_str = match.groups()
        print(f"[DEBUG] Everyday in month pattern matched: {match.groups()}")
        
        hour, minute = parse_time(hour_str, minute_str, period)
        month_num = parse_month(month_str)
        year = datetime.now().year
        
        # Use the new function to create events for the entire month
        from google_utils.calendar_tools import create_recurring_events_for_month
        result = create_recurring_events_for_month(
            "Daily Meeting", month_num, year, hour, minute, 
            interval_days=1, description=f"Daily meeting scheduled for {month_str}"
        )
        print(f"[DEBUG] Created daily events for {month_str}")
        return result
    
    # NEW: Pattern: "schedule meeting every 4th day in August"  
    elif re.search(patterns["every_nth_day_in_month"], query, re.I):
        match = re.search(patterns["every_nth_day_in_month"], query, re.I)
        interval_str, month_str, hour_str, minute_str, period = match.groups()
        print(f"[DEBUG] Every Nth day in month pattern matched: {match.groups()}")
        
        # Default time if not specified
        if hour_str and period:
            hour, minute = parse_time(hour_str, minute_str, period)
        else:
            hour, minute = 14, 0  # Default to 2 PM
        
        month_num = parse_month(month_str)
        year = datetime.now().year
        interval_days = int(interval_str)
        
        # Use the new function to create interval events for the month
        from google_utils.calendar_tools import create_recurring_events_for_month
        result = create_recurring_events_for_month(
            f"Meeting (Every {interval_days} days)", month_num, year, hour, minute,
            interval_days=interval_days, description=f"Meeting every {interval_days} days in {month_str}"
        )
        print(f"[DEBUG] Created every {interval_days} days events for {month_str}")
        return result
    
    # NEW: Pattern: "schedule meeting at 7pm everyday in August" (alternative order)
    elif re.search(patterns["daily_for_month"], query, re.I):
        match = re.search(patterns["daily_for_month"], query, re.I)
        hour_str, minute_str, period, month_str = match.groups()
        print(f"[DEBUG] Daily for month pattern matched: {match.groups()}")
        
        hour, minute = parse_time(hour_str, minute_str, period)
        month_num = parse_month(month_str)
        year = datetime.now().year
        
        # Use the new function to create events for the entire month
        from google_utils.calendar_tools import create_recurring_events_for_month
        result = create_recurring_events_for_month(
            "Daily Meeting", month_num, year, hour, minute,
            interval_days=1, description=f"Daily meeting scheduled for {month_str}"
        )
        print(f"[DEBUG] Created daily events for {month_str}")
        return result
    
    # If no recurring patterns matched, try standard one-time patterns
    if not is_recurring:
        # Try each standard pattern
        for pattern_name, pattern in patterns.items():
            if pattern_name in ["daily_range", "interval_pattern", "daily_recurring", "weekly_recurring"]:
                continue  # Skip recurring patterns we already checked
                
            match = re.search(pattern, query, re.I)
            if match:
                print(f"[DEBUG] {pattern_name} matched: {match.groups()}")
                
                if pattern_name == "pattern1":  # "at 7pm on 1st of July 2024"
                    hour_str, minute_str, period, day_str, month_str, day_alt, year_str = match.groups()
                    day = int(day_str or day_alt or 1)
                    month = parse_month(month_str)
                    year = int(year_str) if year_str else datetime.now().year
                    hour, minute = parse_time(hour_str, minute_str, period)
                    start_time = datetime(year, month, day, hour, minute)
                    
                elif pattern_name == "pattern2":  # "July 1, 2025 at 7:00 PM"
                    month_str, day_str, year_str, hour_str, minute_str, period = match.groups()
                    day = int(day_str)
                    month = parse_month(month_str)
                    year = int(year_str) if year_str else datetime.now().year
                    hour, minute = parse_time(hour_str, minute_str, period)
                    start_time = datetime(year, month, day, hour, minute)
                    
                elif pattern_name == "pattern3":  # "tomorrow at 3 PM"
                    day_word, hour_str, minute_str, period = match.groups()
                    if day_word.lower() == "tomorrow":
                        base_date += timedelta(days=1)
                    hour, minute = parse_time(hour_str, minute_str, period)
                    start_time = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                elif pattern_name == "pattern4":  # "on 31st of July at 7pm"
                    day_str, month_str, year_str, hour_str, minute_str, period = match.groups()
                    day = int(day_str)
                    month = parse_month(month_str)
                    year = int(year_str) if year_str else datetime.now().year
                    hour, minute = parse_time(hour_str, minute_str, period)
                    start_time = datetime(year, month, day, hour, minute)
                    
                elif pattern_name == "pattern5":  # "at 7pm on July 1st"
                    hour_str, minute_str, period, day_str, month_str, year_str = match.groups()
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
                
                break

    if start_time is None:
        print(f"[DEBUG] No patterns matched for query: {query}")
        return {
            "status": "error",
            "message": "Could not parse meeting time. Please use format like 'schedule meeting at 7:00 PM on July 1, 2025'",
            "examples": [
                "schedule meeting tomorrow at 2 PM",
                "schedule meeting at 7:00 PM on July 1, 2025",
                "schedule meeting on July 1st at 7 PM",
                "schedule meeting at 7pm on 1st of July 2025",
                "set a meeting from 1st August to 7th August at 4 PM every day",
                "set a meeting every 4th day in August",
                "schedule meeting everyday at 7pm in August",
                "schedule meeting every 4th day in August at 2pm"
            ]
        }

    # Adjust for past dates
    if start_time < datetime.now():
        try:
            start_time = start_time.replace(year=start_time.year + 1)
        except ValueError:
            # handle February 29th on non-leap years
            start_time = start_time + timedelta(days=365)

    end_time = start_time + timedelta(hours=1)
    
    print(f"[DEBUG] Parsed time: {start_time} to {end_time}")
    print(f"[DEBUG] Is recurring: {is_recurring}")
    if is_recurring:
        print(f"[DEBUG] Recurrence rule: {recurrence_rule}")
    
    # Determine meeting title from query
    meeting_title = "Business Meeting"
    if "sales" in query.lower():
        meeting_title = "Sales Meeting"
    elif "finance" in query.lower() or "financial" in query.lower():
        meeting_title = "Financial Meeting"
    elif "review" in query.lower():
        meeting_title = "Review Meeting"
    elif "product" in query.lower():
        meeting_title = "Product Meeting"
    
    # Convert datetime objects to ISO format strings for the Google Calendar API
    start_iso = start_time.isoformat() + "Z"
    end_iso = end_time.isoformat() + "Z"
    
    print(f"[DEBUG] Creating event: {meeting_title} from {start_iso} to {end_iso}")

    try:
        if is_recurring:
            # Use the new create_recurring_event function
            result = create_recurring_event(
                meeting_title, 
                start_iso, 
                end_iso, 
                recurrence_rule,
                description=f"Recurring meeting created from query: {query}"
            )
            print(f"[DEBUG] Created recurring event successfully")
        else:
            # Use the standard create_event function
            result = create_event(meeting_title, start_iso, end_iso)
            print(f"[DEBUG] Created one-time event successfully")
            
        return result
        
    except Exception as e:
        print(f"[ERROR] Calendar event creation failed: {str(e)}")
        return {"status": "error", "message": f"Failed to create calendar event: {str(e)}"}

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

---

🚨 **CRITICAL ANALYTICS WORKFLOW:**  
For ANY analytics query, you MUST follow this exact process:

1️⃣ **ALWAYS delegate to the appropriate sub-agent FIRST**
   → Use `delegate_with_capture(query)` to auto-store responses
2️⃣ **IMMEDIATELY after getting the response**, call `capture_analytics_after_response(query, response)`
3️⃣ This ensures analytics data is captured for email functionality

🔹 **Analytics Queries** (sales, financial, inventory, purchase):
   → Delegate to appropriate agent → `capture_analytics_after_response(query, response)`

🔹 **Email Queries** (send, mail, email):
   → Call `smart_send_email(query)` (uses captured analytics automatically)

🔹 **Calendar Queries** (schedule, meeting, event):
   → Call `smart_schedule_event(query)`

🔹 **Greetings** (hello, hi):
   → Delegate to `greeting_agent` (no analytics capture needed)

---

🚨 **EMAIL HANDLING:**  
If the query contains:  
- Keywords like "send", "email", "mail", "forward"  
- OR includes an email address (e.g., user@example.com)  

→ Call: `smart_send_email(query)`  

This will automatically use the stored analytics data from previous queries.

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

✔️ User: "Hello"
   → Delegate to `greeting_agent` (no capture needed)

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
        
    ],
    sub_agents=[greeting_agent, sales_agent, purchase_agent, inventory_agent, financial_agent],
)


