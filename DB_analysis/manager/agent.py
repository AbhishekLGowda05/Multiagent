from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
import os, sys, re, json, traceback, base64, random
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Any

#  Add Int-Assignment root path so google_utils is discoverable
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))  # Goes up to Int-Assignment

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Guard against unfinished YAML-based configurations
for env_var in os.environ:
    if "AGENT" in env_var and "YAML" in env_var:
        raise RuntimeError(
            f"YAML agent configuration via '{env_var}' is not supported; agents must be defined programmatically."
        )

#  Import Google utilities (now will work inside ADK)
from google_utils.gmail_tools import send_email, read_emails
from google_utils.calendar_tools import (
    create_event,
     create_recurring_event,
     build_daily_rrule,
     build_interval_rrule,
)

# Chart generation utility
# from visualization_utils import generate_chart  # Comment out to use local version

#  Import sub-agents (fixed import paths)
from .sub_agents.sales_agent.agent import sales_agent
from .sub_agents.greeting_agent.agent import greeting_agent
from .sub_agents.purchase_agent.agent import purchase_agent
from .sub_agents.inventory_agent.agent import inventory_agent
from .sub_agents.financial_agent.agent import financial_agent

#  Cross-agent orchestrator
from .cross_agent_orchestrator import CrossAgentOrchestrator, DEFAULT_SPECS
cross_orchestrator = CrossAgentOrchestrator(DEFAULT_SPECS)

#  Memory for last analytics result
LAST_ANALYTICS_RESULT: str = ""
LAST_ANALYTICS_DATA: dict = {}

#  NEW: Query Preprocessor - Intercepts emails BEFORE LLM processing
def preprocess_query(query: str) -> tuple[str, bool]:
    """
    Preprocessor that intercepts email requests before they reach the LLM.
    Returns (possibly_modified_query, should_continue_to_llm)
    """
    print(f"[PREPROCESSOR] ===== QUERY INTERCEPTOR =====")
    print(f"[PREPROCESSOR] Original query: {query}")

    query_lower = query.lower().strip()

    # Check for analytics or cross-agent indicators
    analytics_keywords = [
        "analysis", "analytics", "report", "insight", "chart",
        "graph", "compare", "comparison", "summary", "trend"
    ]
    has_analytics = is_cross_agent_query(query) or any(
        keyword in query_lower for keyword in analytics_keywords
    )

    # Email detection patterns
    email_patterns = [
        # Primary patterns
        ("send" in query_lower and ("mail" in query_lower or "email" in query_lower)),
        # Email address pattern
        ("@" in query and re.search(r'\b[\w.+-]+@[\w.-]+\.\w+\b', query)),
        # Direct mail commands
        ("mail this to" in query_lower),
        ("forward to" in query_lower),
        ("email this to" in query_lower)
    ]

    is_email_request = any(email_patterns)

    if is_email_request:
        if has_analytics:
            print(f"[PREPROCESSOR] Email contains analytics indicators; deferring to LLM")
            return query, True

        print(f"[PREPROCESSOR]  EMAIL REQUEST DETECTED!")
        print(f"[PREPROCESSOR] Executing smart_send_email immediately...")

        try:
            # Execute email function directly
            email_result = smart_send_email(query)

            # Create response based on email result
            if email_result.get('status') == 'completed':
                response = f" Email sent successfully to {email_result.get('recipients', 0)} recipient(s). Message ID: {email_result.get('results', [{}])[0].get('result', {}).get('id', 'unknown')}"
            else:
                response = f" Email failed: {email_result.get('message', 'Unknown error')}"

            print(f"[PREPROCESSOR] Email result: {email_result.get('status')}")
            print(f"[PREPROCESSOR] Returning direct response, bypassing LLM")

            # Return the response and indicate NOT to continue to LLM
            return response, False

        except Exception as e:
            print(f"[PREPROCESSOR] Email execution error: {e}")
            error_response = f" Email processing failed: {str(e)}"
            return error_response, False
    
    # Calendar detection patterns
    calendar_patterns = [
        ("schedule" in query_lower and ("meeting" in query_lower or "event" in query_lower)),
        ("create event" in query_lower),
        ("book meeting" in query_lower),
        ("add to calendar" in query_lower)
    ]
    
    is_calendar_request = any(calendar_patterns)
    
    if is_calendar_request:
        print(f"[PREPROCESSOR]  CALENDAR REQUEST DETECTED!")
        print(f"[PREPROCESSOR] Executing smart_schedule_event immediately...")
        
        try:
            # Execute calendar function directly
            calendar_result = smart_schedule_event(query)
            
            # Create response based on calendar result
            if calendar_result.get('status') == 'success':
                response = f" Calendar event created successfully: {calendar_result.get('message', 'Event scheduled')}"
            else:
                response = f" Calendar event failed: {calendar_result.get('message', 'Unknown error')}"
            
            print(f"[PREPROCESSOR] Calendar result: {calendar_result.get('status')}")
            print(f"[PREPROCESSOR] Returning direct response, bypassing LLM")
            
            # Return the response and indicate NOT to continue to LLM
            return response, False
            
        except Exception as e:
            print(f"[PREPROCESSOR] Calendar execution error: {e}")
            error_response = f" Calendar processing failed: {str(e)}"
            return error_response, False
    
    print(f"[PREPROCESSOR] No email/calendar patterns detected, continuing to LLM")
    return query, True

#  NEW: Format cross-agent results for display
def format_cross_agent_result(result: dict, query: str) -> str:
    """
    Format cross-agent orchestrator results into a human-readable response.
    """
    if not isinstance(result, dict):
        return str(result)
    
    # Extract metadata
    metadata = result.get("_metadata", {})
    agents_triggered = metadata.get("agents_triggered", [])
    execution_log = metadata.get("execution_log", [])
    cross_analysis = metadata.get("cross_agent_analysis", {})
    
    # Build formatted response
    lines = []
    lines.append(f" CROSS-AGENT ANALYSIS: {query}")
    lines.append("=" * 60)
    
    # Add agent results
    for agent_name, agent_data in result.items():
        if agent_name.startswith("_"):  # Skip metadata
            continue
            
        lines.append(f"\n {agent_name.upper()} RESULTS:")
        lines.append("-" * 30)
        
        for tool_name, tool_data in agent_data.items():
            if isinstance(tool_data, dict):
                if "error" in tool_data:
                    lines.append(f" {tool_name}: {tool_data['error']}")
                else:
                    # Format tool results
                    lines.append(f" {tool_name}:")
                    for key, value in tool_data.items():
                        if key not in ["error", "status"]:
                            lines.append(f"    {key}: {value}")
            else:
                lines.append(f" {tool_name}: {tool_data}")
    
    # Add cross-agent insights
    if cross_analysis:
        lines.append(f"\n CROSS-DOMAIN INSIGHTS:")
        lines.append("-" * 30)
        
        summary = cross_analysis.get("summary", "")
        if summary:
            lines.append(f" Summary: {summary}")
            
        key_findings = cross_analysis.get("key_findings", [])
        if key_findings:
            lines.append("\n Key Findings:")
            for finding in key_findings[:5]:  # Limit to top 5
                lines.append(f"    {finding}")
        
        recommendations = cross_analysis.get("recommendations", [])
        if recommendations:
            lines.append("\n Recommendations:")
            for rec in recommendations[:3]:  # Limit to top 3
                lines.append(f"    {rec}")
    
    lines.append("\n" + "=" * 60)
    lines.append(f" Analysis completed across {len(agents_triggered)} business domains")
    lines.append(f" Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(lines)

#  NEW: Cross-agent query handler
def handle_cross_agent_query(query: str) -> str:
    """
    Handle queries that require coordination across multiple agents.
    Uses the CrossAgentOrchestrator to determine which agents are needed.
    """
    print(f"[DEBUG] ===== CROSS-AGENT QUERY HANDLER =====")
    print(f"[DEBUG] Query: {query}")
    
    try:
        # Use orchestrator to handle the cross-agent query
        result = cross_orchestrator.handle_query(query)
        print(f"[DEBUG] Cross-agent orchestrator result: {str(result)[:200]}...")
        
        # Format the result for display
        formatted_result = format_cross_agent_result(result, query)

        # Capture the result for potential email use
        global LAST_ANALYTICS_RESULT, LAST_ANALYTICS_DATA
        LAST_ANALYTICS_RESULT = formatted_result

        # Try to extract structured data if possible
        if isinstance(result, dict):
            LAST_ANALYTICS_DATA = result
        else:
            LAST_ANALYTICS_DATA = {"cross_agent_result": str(result)}

        print(f"[DEBUG]  Cross-agent result captured for email use")

        # NEW: Detect direct email requests in the original query
        email_status = ""
        try:
            if re.search(r'\b[\w.+-]+@[\w.-]+\.\w+\b', query):
                print(f"[DEBUG]  Email address detected - executing smart_send_email")
                email_result = smart_send_email(query)
                status = email_result.get('status', 'unknown')
                message = email_result.get('message', '')
                email_status = f"\nEmail Status: {status}"
                if message:
                    email_status += f" - {message}"
        except Exception as email_error:
            print(f"[DEBUG]  Email sending error: {email_error}")
            email_status = f"\nEmail Error: {email_error}"

        return formatted_result + email_status
        
    except Exception as e:
        error_msg = f"Error in cross-agent orchestration: {str(e)}"
        print(f"[DEBUG]  Cross-agent error: {error_msg}")
        return error_msg

#  NEW: Detect if query needs multiple agents
def is_cross_agent_query(query: str) -> bool:
    """
    Determine if a query requires coordination across multiple agents.
    """
    query_lower = query.lower()
    
    # Keywords that suggest cross-agent coordination is needed
    cross_agent_indicators = [
        # Comparison between domains
        "compare", "comparison", "vs", "versus", "against",
        
        # Multi-domain keywords in single query
        "sales and inventory", "sales and financial", "inventory and purchase",
        "customers and payment", "revenue and stock", "profit and sales",
        
        # Analysis spanning domains
        "top customers by sales volume with their payment",
        "sales performance and inventory levels",
        "revenue trends and purchase patterns",
        "customer behavior and financial impact",
        
        # Cross-domain reports
        "comprehensive report", "full analysis", "complete overview",
        "business summary", "performance across"
    ]
    
    # Multi-agent keyword combinations
    agent_keywords = {
        "sales": ["sales", "customer", "invoice", "revenue"],
        "financial": ["financial", "profit", "expense", "payment", "cash"],
        "inventory": ["inventory", "stock", "item", "product"],
        "purchase": ["purchase", "vendor", "supplier", "buy"]
    }
    
    # Check for cross-domain indicators
    if any(indicator in query_lower for indicator in cross_agent_indicators):
        return True
    
    # Check if query mentions keywords from multiple domains
    domains_mentioned = 0
    for domain, keywords in agent_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            domains_mentioned += 1
    
    # If 2+ domains mentioned, it's likely a cross-agent query
    if domains_mentioned >= 2:
        return True
    
    return False

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
            
        elif "profit_analysis" in analytics_data:
            # Create profit analysis chart
            categories = list(analytics_data["profit_analysis"].keys())
            amounts = list(analytics_data["profit_analysis"].values())
            
            plt.figure(figsize=(10, 6))
            colors = ['green' if cat == 'Profit' else 'red' if cat == 'Purchases' else 'blue' for cat in categories]
            bars = plt.bar(categories, amounts, color=colors)
            plt.title("Financial Analysis", fontsize=16, fontweight='bold')
            plt.ylabel("Amount ($)")
            plt.xticks(rotation=45)
            
            # Format y-axis to show currency
            plt.ticklabel_format(style='plain', axis='y')
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'${height:,.0f}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close()
            
        elif "financial_comparison" in analytics_data:
            # Create financial comparison chart (e.g., Cash Inflow vs Profit)
            categories = list(analytics_data["financial_comparison"].keys())
            amounts = list(analytics_data["financial_comparison"].values())
            
            plt.figure(figsize=(10, 6))
            colors = ['#2E86AB', '#A23B72']  # Blue for Cash Inflow, Purple for Profit
            bars = plt.bar(categories, amounts, color=colors)
            plt.title("Financial Comparison", fontsize=16, fontweight='bold')
            plt.ylabel("Amount ($)")
            
            # Format y-axis to show currency
            plt.ticklabel_format(style='plain', axis='y')
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'${height:,.0f}', ha='center', va='bottom')
            
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
            
        elif "monthly_sales" in analytics_data:
            # Create monthly sales trend chart
            months = list(analytics_data["monthly_sales"].keys())
            amounts = list(analytics_data["monthly_sales"].values())
            
            plt.figure(figsize=(12, 8))
            plt.plot(months, amounts, marker='o', linewidth=2, markersize=8, color='#2E86AB')
            plt.fill_between(months, amounts, alpha=0.3, color='#2E86AB')
            plt.title("Monthly Sales Trend", fontsize=16, fontweight='bold')
            plt.xlabel("Month")
            plt.ylabel("Sales Amount ($)")
            plt.xticks(rotation=45)
            
            # Format y-axis to show currency
            plt.ticklabel_format(style='plain', axis='y')
            plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close()
        
        else:
            # Generic chart for any other analytics data
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, 'Analytics Chart\nData visualization available', 
                    ha='center', va='center', fontsize=16, transform=plt.gca().transAxes)
            plt.title("Analytics Report", fontsize=16, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(path, dpi=300, bbox_inches='tight')
            plt.close()
    
    else:
        # No data provided, create a placeholder chart
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'Chart not available\nNo analytics data provided', 
                ha='center', va='center', fontsize=16, transform=plt.gca().transAxes)
        plt.title("Analytics Report", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
    
    return path


def _create_pdf(text: str, chart_path: str, pdf_path: str = "report.pdf") -> str:
    """Generate a simple PDF containing text and an optional chart."""
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import textwrap

    with PdfPages(pdf_path) as pdf:
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")
        
        # Wrap text manually since matplotlib doesn't support wrap=True
        wrapped_text = textwrap.fill(text, width=80)
        ax.text(0.05, 0.95, wrapped_text, va="top", ha="left", fontsize=10, 
                transform=ax.transAxes)
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

        if os.path.exists(chart_path):
            img = plt.imread(chart_path)
            fig, ax = plt.subplots()
            ax.imshow(img)
            ax.axis("off")
            pdf.savefig(fig, bbox_inches='tight')
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


#  NEW: Universal analytics detection and capture hook
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
        print(f"[DEBUG]  ANALYTICS DETECTED - Auto-capturing response")
        
        # Auto-format and store the response
        formatted_response = format_and_store_agent_response(str(response))
        
        print(f"[DEBUG]  Analytics auto-capture completed")
        return response
    else:
        print(f"[DEBUG]  No analytics detected - skipping auto-capture")
        return response

# Remove or comment out the problematic line around line 294

# Add this function after the existing capture_analytics_after_response function

#  ENHANCED: Format agent response with improved regex patterns and analytics capture
def format_and_store_agent_response(response: str) -> str:
    """Format agent response and store it for email use with robust data extraction."""
    print(f"[DEBUG] ===== FORMATTING AGENT RESPONSE =====")
    print(f"[DEBUG] Response type: {type(response)}")
    print(f"[DEBUG] Response length: {len(str(response))}")
    print(f"[DEBUG] Response preview: {str(response)[:300]}...")
    
    # Parse analytics data from response for chart generation
    analytics_data = {}
    response_str = str(response)
    
    #  NEW: Handle JSON responses from sales agent
    if "get_sales_summary_response" in response_str or "{" in response_str and "result" in response_str:
        print(f"[DEBUG] Detected JSON response - attempting to parse and format")
        try:
            # Try to parse as JSON
            if response_str.strip().startswith("{"):
                json_data = json.loads(response_str)
            else:
                # Extract JSON from string if embedded
                json_match = re.search(r'\{.*\}', response_str, re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group())
                else:
                    json_data = None
            
            if json_data:
                # Extract sales data from JSON
                result_data = None
                if "get_sales_summary_response" in json_data:
                    result_data = json_data["get_sales_summary_response"]["result"]
                elif "result" in json_data:
                    result_data = json_data["result"]
                    
                if result_data:
                    print(f"[DEBUG] Parsing JSON sales data: {result_data}")
                    
                    # Format top customers from JSON
                    formatted_response = " SALES SUMMARY REPORT\n===============================\n\nTop Customers:\n\n"
                    
                    if "top_customers" in result_data:
                        top_customers = {}
                        for customer_data in result_data["top_customers"]:
                            customer_name = customer_data[0]
                            invoice_count = customer_data[1]
                            formatted_response += f"{customer_name}: {invoice_count}\n"
                            top_customers[customer_name] = invoice_count
                        
                        analytics_data["top_customers"] = top_customers
                        print(f"[DEBUG] Extracted top customers from JSON: {top_customers}")
                    
                    # Add total invoices
                    if "total_invoices" in result_data:
                        formatted_response += f"\nTotal Invoices: {result_data['total_invoices']}"
                    
                    # Add voucher types
                    if "voucher_types" in result_data and result_data["voucher_types"]:
                        voucher_type = result_data["voucher_types"][0]
                        formatted_response += f" Voucher Types: {voucher_type[0]} ({voucher_type[1]})"
                    
                    formatted_response += f"\n\n=====================================\nReport generated successfully \nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    print(f"[DEBUG] Formatted JSON response into readable format")
                    response_str = formatted_response  # Use the formatted version for further processing
                    
        except Exception as json_error:
            print(f"[DEBUG] JSON parsing failed: {json_error}, treating as regular text")
    
    # Extract top customers data with flexible regex patterns (for non-JSON responses)
    if not analytics_data and ("customer" in response_str.lower() or "invoice" in response_str.lower()):
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
    if any(word in response_str.lower() for word in ["revenue", "profit", "expense", "income", "financial", "sales drop", "sales trend", "monthly sales", "purchases", "profits drop", "cash inflow", "cash outflow", "inflow", "outflow"]):
        # Enhanced financial pattern: "Revenue: $1000", "Profit - 500", "Expenses (200)"
        # Also handle: "2023-08: 13,595,891.35", "2023-09: 9,454,054.5"
        # Also handle: "profit in January was 8484745.49, with total purchases of 129428132.86"
        # NEW: Handle "Cash inflow in September was 159553857.94, while the profit was 8484745.49"
        
        # Pattern 1: "Cash inflow was X, while profit was Y"
        cash_profit_pattern = r"cash\s+inflow.*?was\s+([\d,.]+).*?profit.*?was\s+([\d,.]+)"
        cash_profit_match = re.search(cash_profit_pattern, response_str, re.IGNORECASE)
        if cash_profit_match:
            cash_inflow, profit = cash_profit_match.groups()
            # Clean up the numbers (remove commas and trailing periods)
            cash_inflow = cash_inflow.rstrip('.').replace(',', '')
            profit = profit.rstrip('.').replace(',', '')
            analytics_data["financial_comparison"] = {
                "Cash Inflow": float(cash_inflow),
                "Profit": float(profit)
            }
            print(f"[DEBUG] Extracted cash inflow vs profit data: {analytics_data['financial_comparison']}")
        
        # Pattern 2: General financial pattern (only if we didn't find comparison data)
        if not analytics_data.get("financial_comparison"):
            financial_pattern = r"(revenue|profit|expense|income|sales|purchases?|2023-\d+|january|february|march|april|may|june|july|august|september|october|november|december)[:\s]+(?:was\s+|in\s+\w+\s+was\s+)?(\d+(?:,\d+)*(?:\.\d+)?)"
            matches = re.findall(financial_pattern, response_str, re.IGNORECASE)
            if matches:
                financial_summary = {}
                for category, amount in matches:
                    # Clean up the category name
                    if category.startswith("2023-"):
                        category = f"Month {category}"  # Convert "2023-08" to "Month 2023-08"
                    elif category.lower() in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]:
                        category = f"{category.title()} Data"
                    financial_summary[category.title()] = float(amount.replace(',', ''))
                if financial_summary:
                    analytics_data["financial_summary"] = financial_summary
                    print(f"[DEBUG] Extracted financial data: {financial_summary}")
        
        # Special pattern for profit analysis responses like your January example (only if no other data found)
        if not analytics_data.get("financial_comparison") and not analytics_data.get("financial_summary"):
            profit_analysis_pattern = r"profit.*?(\d+(?:,\d+)*(?:\.\d+)?).*?purchases.*?(\d+(?:,\d+)*(?:\.\d+)?).*?sales.*?(\d+(?:,\d+)*(?:\.\d+)?)"
            profit_match = re.search(profit_analysis_pattern, response_str, re.IGNORECASE)
            if profit_match:
                profit, purchases, sales = profit_match.groups()
                analytics_data["profit_analysis"] = {
                    "Profit": float(profit.replace(',', '')),
                    "Purchases": float(purchases.replace(',', '')),
                    "Sales": float(sales.replace(',', ''))
                }
                print(f"[DEBUG] Extracted profit analysis data: {analytics_data['profit_analysis']}")
        
        # Also check for sales trend data in the format "2023-08: 13,595,891.35"
        trend_pattern = r"(\d{4}-\d{2}):\s*([\d,]+\.?\d*)"
        trend_matches = re.findall(trend_pattern, response_str)
        if trend_matches:
            monthly_sales = {}
            for month, amount in trend_matches:
                monthly_sales[month] = float(amount.replace(',', ''))
            if monthly_sales:
                analytics_data["monthly_sales"] = monthly_sales
                print(f"[DEBUG] Extracted monthly sales data: {monthly_sales}")
    
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
        emoji = "[SALES]"
    elif any(word in response_str.lower() for word in ["financial", "profit", "revenue", "expense"]):
        report_type = "FINANCIAL ANALYSIS"
        emoji = "[FINANCIAL]"
    elif any(word in response_str.lower() for word in ["inventory", "stock", "item"]):
        report_type = "INVENTORY ANALYSIS"
        emoji = "[INVENTORY]"
    elif any(word in response_str.lower() for word in ["purchase", "vendor", "supplier"]):
        report_type = "PURCHASE ANALYSIS"
        emoji = "[PURCHASE]"
    else:
        report_type = "BUSINESS ANALYSIS"
        emoji = "[BUSINESS]"
    
    # Create formatted email body that matches ADK web display
    # Use the formatted response_str if it was already formatted from JSON
    if "Report generated successfully " in response_str:
        formatted_result = response_str  # Already formatted
    else:
        formatted_result = f"""{emoji} {report_type} REPORT
{'=' * (len(report_type) + 10)}

{str(response)}

{'=' * 40}
Report generated successfully 
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

#  NEW: Auto-wrapper for delegation with analytics capture
def auto_capture_delegation_response(original_query: str, sub_agent_name: str, sub_agent_response: str) -> str:
    """
    Wrapper function to automatically capture analytics after any sub-agent delegation.
    This ensures no analytics queries are missed.
    """
    print(f"[DEBUG] ===== AUTO-CAPTURE DELEGATION WRAPPER =====")
    print(f"[DEBUG] Original query: {original_query}")
    print(f"[DEBUG] Sub-agent: {sub_agent_name}")
    print(f"[DEBUG] Response preview: {str(sub_agent_response)[:200]}...")
    
    # Check if this was an analytics query
    query_lower = original_query.lower()
    is_analytics = any(keyword in query_lower for keyword in [
        "financial", "profit", "revenue", "expense", "income", "summary",
        "sales", "customer", "invoice", "report", "analysis",
        "inventory", "stock", "item", "product",
        "purchase", "vendor", "supplier", "drop", "trend"
    ])
    
    analytics_agents = ["financial_agent", "sales_agent", "inventory_agent", "purchase_agent"]
    is_analytics_agent = sub_agent_name in analytics_agents
    
    if is_analytics or is_analytics_agent:
        print(f"[DEBUG]  Analytics delegation detected - auto-capturing response")
        format_and_store_agent_response(sub_agent_response)
        print(f"[DEBUG]  Auto-capture completed for {sub_agent_name}")
    else:
        print(f"[DEBUG] Non-analytics delegation - skipping capture")
    
    #  NEW: Automatic delegation detection and execution
    response_lower = str(sub_agent_response).lower()
    
    # Delegation patterns from sub-agents
    delegation_patterns = [
        "this request involves sending an email or scheduling an event, which i cannot handle. delegating to the root agent",
        "i'll delegate this email request to the manager agent who has email capabilities",
        "delegating to the root agent",
        "delegate to manager agent", 
        "delegate to root agent"
    ]
    
    # Check if sub-agent is delegating back to manager
    is_delegation = any(pattern in response_lower for pattern in delegation_patterns)
    
    if is_delegation:
        print(f"[DEBUG]  DELEGATION DETECTED from {sub_agent_name}!")
        
        # Email patterns in original query
        email_patterns = ["send this mail to", "send email to", "email this to", "mail this to", "@"]
        calendar_patterns = ["schedule meeting", "create event", "add to calendar", "book meeting"]
        
        is_email_request = any(pattern in original_query.lower() for pattern in email_patterns)
        is_calendar_request = any(pattern in original_query.lower() for pattern in calendar_patterns)
        
        if is_email_request:
            print(f"[DEBUG]  Email delegation detected - executing smart_send_email")
            email_result = smart_send_email(original_query)
            print(f"[DEBUG]  Email executed with result: {email_result}")
            return f" Email delegation handled automatically. {email_result}"
        elif is_calendar_request:
            print(f"[DEBUG]  Calendar delegation detected - calendar functionality not implemented")
            return f"Calendar functionality is not currently implemented. Delegation detected from {sub_agent_name}."
        else:
            # Try to detect email addresses in query
            import re
            if re.search(r'\b[\w.+-]+@[\w.-]+\.\w+\b', original_query):
                print(f"[DEBUG]  Email address found - executing smart_send_email")
                email_result = smart_send_email(original_query)
                print(f"[DEBUG]  Email executed with result: {email_result}")
                return f" Email delegation handled automatically. {email_result}"
            else:
                print(f"[DEBUG]  Delegation detected but no clear email/calendar pattern")
                return f"Delegation detected from {sub_agent_name} but unable to determine action type."
    
    print(f"[DEBUG] ===== AUTO-CAPTURE WRAPPER COMPLETED =====")
    return sub_agent_response

#  ENHANCED: Email tool with better debugging and manual analytics population

def smart_send_email(query: str) -> dict:
    """Send email based on natural language query with memory of last analytics result."""
    print(f"[DEBUG] ===== EMAIL FUNCTION CALLED =====")
    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] LAST_ANALYTICS_RESULT length: {len(LAST_ANALYTICS_RESULT)}")
    print(f"[DEBUG] LAST_ANALYTICS_RESULT first 500 chars: {LAST_ANALYTICS_RESULT[:500]}")
    print(f"[DEBUG] LAST_ANALYTICS_RESULT type: {type(LAST_ANALYTICS_RESULT)}")
    
    try:
        # DEBUG: Check if analytics data is missing
        if not LAST_ANALYTICS_RESULT or len(LAST_ANALYTICS_RESULT.strip()) == 0:
            print(f"[DEBUG] No analytics data found - email will use placeholder data")
            
        # Extract multiple email addresses for multi-recipient support
        pattern1 = re.search(r"(?:send|mail) (?:this|these|mail|email) to ([\w.+-@\s,]+)", query, re.I)
        pattern2 = re.search(r"send (?:an )?email to ([\w.+-@\s,]+)", query, re.I)
        pattern3 = re.search(r"send this mail to ([\w.+-@\s,]+)", query, re.I)  # New pattern for "send this mail to"
        pattern4 = re.search(r"([\w.+-]+@[\w.-]+\.\w+)", query, re.I)
        
        email_addresses = []
        if pattern1:
            email_text = pattern1.group(1)
            subject = "Business Analysis Results"
            print(f"[DEBUG] Pattern 1 matched - Email text: {email_text}")
        elif pattern2:
            email_text = pattern2.group(1)
            subject = "Business Report"
            print(f"[DEBUG] Pattern 2 matched - Email text: {email_text}")
        elif pattern3:
            email_text = pattern3.group(1)
            subject = "Business Analysis Results"
            print(f"[DEBUG] Pattern 3 matched - Email text: {email_text}")
        elif pattern4:
            email_text = query
            subject = "Analytics Report"
            print(f"[DEBUG] Pattern 4 matched - Using entire query")
        else:
            email_text = query
            subject = "Analytics Report"
            print(f"[DEBUG] No pattern matched - Using entire query for email extraction")
            
        email_pattern = r"([\w.+-]+@[\w.-]+\.\w+)"
        email_addresses = re.findall(email_pattern, email_text)
        if not email_addresses:
            print(f"[DEBUG] No email addresses found")
            return {"status": "error", "message": "No email address found in query"}
            
        print(f"[DEBUG] Found {len(email_addresses)} email addresses: {email_addresses}")
        
        if not LAST_ANALYTICS_RESULT or len(LAST_ANALYTICS_RESULT.strip()) == 0:
            error_msg = "No analytics data captured! To send a meaningful email with charts and data: 1. First run an analytics query (e.g., 'get sales summary', 'show top customers') 2. Then request the email again. Currently no analytics data is stored in memory."
            print(f"[ERROR] {error_msg}")
            return {"status": "error", "message": error_msg, "suggestion": "Please run an analytics query first, then retry the email request"}
            
        body_text = LAST_ANALYTICS_RESULT
        print(f"[DEBUG] Using stored analytics result, length: {len(body_text)}")
        
        global LAST_ANALYTICS_DATA
        chart_file = None
        has_chart = False
        
        # Try to generate chart if we have analytics data
        if LAST_ANALYTICS_DATA and len(LAST_ANALYTICS_DATA) > 0:
            print(f"[DEBUG] Generating chart with analytics data: {LAST_ANALYTICS_DATA}")
            try:
                chart_file = generate_chart(LAST_ANALYTICS_DATA, path="analytics_chart.png")
                has_chart = True
                print(f"[DEBUG] Chart generated successfully: {chart_file}")
            except Exception as chart_error:
                print(f"[WARNING] Chart generation failed: {chart_error}")
                print(f"[DEBUG] Continuing without chart - email will still be sent")
                has_chart = False
        else:
            print(f"[DEBUG] No analytics data for charts - sending email without chart")
            has_chart = False
            
        attach_pdf = "pdf" in query.lower()
        
        # Create HTML email body - with or without chart
        try:
            # Chart section HTML - only include if we have a chart
            chart_section = ""
            if has_chart and chart_file and os.path.exists(chart_file):
                chart_section = """
    <div class="chart-container">
        <h3 style="color: #555;"> Visual Analysis</h3>
        <img src='cid:chart' alt="Analytics Chart" style="max-width: 100%; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    </div>"""
            else:
                chart_section = """
    <div class="chart-container">
        <h3 style="color: #555;"> Analysis Report</h3>
        <p style="color: #666; font-style: italic;">Chart visualization not available for this data type</p>
    </div>"""

            html_body = f"""<!DOCTYPE html>
<html>
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
    {chart_section}
    
    <div class="footer">
        Generated by Business Analytics System<br>
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>"""
        except Exception as html_error:
            print(f"[ERROR] HTML body generation failed: {html_error}")
            return {"status": "error", "message": f"HTML body generation failed: {html_error}"}
            
        # Prepare attachments - only include chart if it exists
        attachments = []
        if has_chart and chart_file and os.path.exists(chart_file):
            attachments.append(chart_file)
            
        if attach_pdf:
            try:
                pdf_path = _create_pdf(body_text, chart_file if has_chart else None)
                attachments.append(pdf_path)
            except Exception as pdf_error:
                print(f"[ERROR] PDF generation failed: {pdf_error}")
                return {"status": "error", "message": f"PDF generation failed: {pdf_error}"}
                
        print(f"[DEBUG] Final email body length: {len(html_body)}")
        print(f"[DEBUG] Final email body preview: {html_body[:200]}...")
        print(f"[DEBUG] Sending email to {len(email_addresses)} recipients with {len(attachments)} attachment(s)...")
        print(f"[SUCCESS] Email contains analytics data - Chart available: {has_chart}")
        
        results = []
        for to_email in email_addresses:
            try:
                print(f"[DEBUG] Attempting to send email to: {to_email}")
                from google_utils.gmail_tools import send_email
                print(f"[DEBUG] Gmail tools imported successfully")
                simple_body = f"{subject}\n\n{body_text}\n\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # Only attach chart if it exists
                attachment_path = chart_file if (has_chart and chart_file and os.path.exists(chart_file)) else None
                
                result = send_email(
                    to_email=to_email,
                    subject=subject,
                    body=simple_body,
                    attachment_path=attachment_path
                )
                print(f"[DEBUG] Email sent to {to_email}, result: {result}")
                results.append({"email": to_email, "status": "sent", "result": result})
            except Exception as email_error:
                print(f"[ERROR] Email processing failed to {to_email}: {str(email_error)}")
                print(f"[ERROR] Email error type: {type(email_error)}")
                print(f"[ERROR] Email error traceback: {traceback.format_exc()}")  # This line should work now
                results.append({"email": to_email, "status": "error", "error": str(email_error)})
                
        print(f"[SUCCESS] Email sending completed - {len(results)} recipients processed")
        print(f"[DEBUG] ===== EMAIL FUNCTION COMPLETED =====")
        return {"status": "completed", "recipients": len(email_addresses), "results": results, "message": f"Processed emails to {len(email_addresses)} recipients with analytics data and charts"}
        
    except Exception as e:
        print(f"[ERROR] Critical error in smart_send_email: {str(e)}")
        print(f"[ERROR] Error type: {type(e)}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        return {"status": "error", "message": f"Email function failed with error: {str(e)}", "error_type": str(type(e)), "suggestion": "Check Google API credentials and email configuration"}


#  NEW: Email reading functionality
def smart_read_last_emails(count: int = 3) -> dict:
    """Return the latest `count` emails from the inbox."""
    print(f"[DEBUG] ===== EMAIL READ FUNCTION CALLED =====")

    try:
        import os

        credentials_path = "./google_utils/credentials.json"
        if os.getenv("MOCK_GOOGLE_APIS") == "true":
            print(f"[DEBUG] Mock mode enabled - retrieving mock emails")
            emails = read_emails(query="in:inbox")
            return {"status": "success", "emails": emails[:count], "mode": "mock"}

        if not os.path.exists(credentials_path):
            print(f"[ERROR] Credentials not found at {credentials_path}")
            return {
                "status": "error",
                "message": f"Google API credentials not found at {credentials_path}",
                "suggestion": "Please ensure credentials.json exists in the google_utils folder",
            }

        print(f"[DEBUG] Fetching inbox emails from Gmail...")
        emails = read_emails(query="in:inbox")
        print(f"[DEBUG] Retrieved {len(emails)} emails")

        return {"status": "success", "emails": emails[:count], "mode": "real"}

    except Exception as e:
        print(f"[ERROR] Email read failed: {str(e)}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"Failed to read emails: {str(e)}",
            "error_type": str(type(e)),
            "suggestion": "Check Google API credentials and Gmail permissions",
        }


#  ENHANCED: Email deletion functionality with better error handling
def smart_delete_last_email() -> dict:
    """Delete the last sent email from the user's account."""
    print(f"[DEBUG] ===== EMAIL DELETION FUNCTION CALLED =====")
    
    try:
        from google_utils.gmail_tools import read_emails, delete_email
        import os
        
        # Check if running in mock mode first
        credentials_path = "./google_utils/credentials.json"
        if os.getenv("MOCK_GOOGLE_APIS") == "true":
            print(f"[DEBUG] Mock mode enabled - simulating email deletion")
            return {
                "status": "success", 
                "message": " [MOCK MODE] Successfully simulated deleting the last sent email.",
                "email_id": "mock_email_deleted",
                "mode": "mock"
            }
        
        if not os.path.exists(credentials_path):
            print(f"[ERROR] Credentials not found at {credentials_path}")
            return {
                "status": "error", 
                "message": f"Google API credentials not found at {credentials_path}",
                "suggestion": "Please ensure credentials.json exists in the google_utils folder"
            }
        
        # Get the last sent email with more specific query
        print(f"[DEBUG] Fetching sent emails from Gmail...")
        sent_emails = read_emails(query="in:sent")
        
        if not sent_emails:
            print(f"[DEBUG] No sent emails found")
            return {"status": "error", "message": "No sent emails found to delete."}
        
        # Get the most recent email (first in the list)
        last_email_id = sent_emails[0]['id']
        print(f"[DEBUG] Found last email ID: {last_email_id}")
        
        # Attempt to delete the email
        print(f"[DEBUG] Attempting to delete email ID: {last_email_id}")
        delete_email(last_email_id)
        
        print(f"[DEBUG]  Successfully deleted email with ID: {last_email_id}")
        return {
            "status": "success", 
            "message": f" Successfully deleted the last sent email (ID: {last_email_id}).",
            "email_id": last_email_id,
            "mode": "real"
        }
        
    except Exception as e:
        print(f"[ERROR] Email deletion failed: {str(e)}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        return {
            "status": "error", 
            "message": f"Failed to delete the last email: {str(e)}",
            "error_details": str(e),
            "suggestion": "Check Google API credentials and Gmail permissions"
        }


#  NEW: Calendar deletion functionality  
def smart_delete_calendar_events(query: str) -> dict:
    """Delete calendar events based on natural language query."""
    print(f"[DEBUG] ===== CALENDAR DELETION FUNCTION CALLED =====")
    print(f"[DEBUG] Query: {query}")
    
    try:
        from google_utils.calendar_tools import list_events, delete_event
        
        # Simple delete patterns
        patterns = {
            "today": r"delete.*(?:meeting|event).*(?:today|for today)",
            "all_today": r"delete all.*(?:meeting|event).*today",
            "last_meeting": r"delete (?:the )?last (?:meeting|event)",
            "by_title": r"delete.*(?:meeting|event).*(?:called|named|titled)\s+['\"]([^'\"]+)['\"]"
        }
        
        events = list_events(max_results=50)  # Get more events for better matching
        deleted_count = 0
        
        for pattern_name, pattern in patterns.items():
            match = re.search(pattern, query, re.I)
            if match:
                print(f"[DEBUG] Matched pattern: {pattern_name}")
                
                if pattern_name == "by_title":
                    title_to_delete = match.group(1).lower()
                    print(f"[DEBUG] Looking for events with title: {title_to_delete}")
                    for event in events:
                        if title_to_delete in event.get('summary', '').lower():
                            delete_event(event['id'])
                            deleted_count += 1
                            print(f"[DEBUG] Deleted event: {event.get('summary', 'Untitled')}")
                            
                elif pattern_name in ["today", "all_today"]:
                    target_date = datetime.now().date()
                    print(f"[DEBUG] Looking for events on: {target_date}")
                    for event in events:
                        if 'start' in event and 'dateTime' in event['start']:
                            event_date = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '')).date()
                            if event_date == target_date:
                                delete_event(event['id'])
                                deleted_count += 1
                                print(f"[DEBUG] Deleted today's event: {event.get('summary', 'Untitled')}")
                                
                elif pattern_name == "last_meeting":
                    if events:
                        last_event = events[0]  # Events are ordered by start time
                        delete_event(last_event['id'])
                        deleted_count += 1
                        print(f"[DEBUG] Deleted last event: {last_event.get('summary', 'Untitled')}")
                
                break
        
        if deleted_count > 0:
            return {
                "status": "success",
                "message": f" Successfully deleted {deleted_count} event(s)",
                "deleted_count": deleted_count
            }
        else:
            return {
                "status": "error",
                "message": "No matching events found to delete. Try: 'delete all meetings today' or 'delete last meeting'"
            }
            
    except Exception as e:
        print(f"[ERROR] Calendar event deletion failed: {str(e)}")
        return {"status": "error", "message": f"Failed to delete calendar events: {str(e)}"}


#  FIXED: Calendar tool with proper signature
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


def smart_generate_image(prompt: str) -> dict:
    """Create a simple image or chart from a text prompt and return the file path."""
    print(f"[DEBUG] ===== IMAGE GENERATION CALLED =====")
    print(f"[DEBUG] Prompt: {prompt}")

    filename = f"generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    try:
        lower_prompt = prompt.lower()

        # If prompt suggests a chart/graph, make a simple bar chart
        if any(word in lower_prompt for word in ["chart", "graph", "plot"]):
            data = [random.randint(1, 10) for _ in range(5)]
            plt.figure()
            plt.bar(range(len(data)), data)
            plt.title(prompt)
        else:
            # Otherwise create a DALL·E-style placeholder image with text
            plt.figure(figsize=(4, 4))
            plt.text(0.5, 0.5, prompt, ha="center", va="center", wrap=True)
            plt.axis("off")

        plt.savefig(filename, bbox_inches="tight")
        plt.close()

        file_path = os.path.abspath(filename)
        print(f"[DEBUG] Image generated at: {file_path}")
        return {"status": "success", "path": file_path}

    except Exception as e:
        print(f"[ERROR] Image generation failed: {e}")
        return {"status": "error", "message": str(e)}


#  NEW: Custom Agent Wrapper with Query Preprocessing
class ManagerAgentWithPreprocessor(Agent):

    """
    Wrapper around the standard Agent that intercepts queries before LLM processing.
    This ensures email/calendar requests are handled immediately without delegation.
    """

    def __init__(self, base_agent: Agent):
        # Initialize the parent Agent class with base agent's properties but without sub_agents
        # to avoid "already has a parent agent" validation error
        super().__init__(
            name=base_agent.name,
            model=base_agent.model,
            description=base_agent.description,
            instruction=base_agent.instruction,
            tools=base_agent.tools,
            sub_agents=[]  # Empty sub_agents to avoid parent conflict
        )
        object.__setattr__(self, "_base_agent", base_agent)
    
    def run(self, query: str, **kwargs):
        """
        Override run method to include preprocessing.
        """
        print(f"[MANAGER] ===== QUERY RECEIVED =====")
        print(f"[MANAGER] Query: {query}")
        
        # Step 1: Preprocess the query
        processed_query, should_continue = preprocess_query(query)
        
        # Step 2: If preprocessor handled it, return the result directly
        if not should_continue:
            print(f"[MANAGER] Preprocessor handled the request directly")
            return processed_query
        
        # Step 3: Otherwise, continue to the base agent (LLM processing)
        print(f"[MANAGER] Continuing to LLM with query: {processed_query}")
        return self._base_agent.run(processed_query, **kwargs)
    
    def run_async(self, query: str, **kwargs):
        """
        Async version for compatibility with ADK agents.
        """
        print(f"[MANAGER] ===== ASYNC QUERY RECEIVED =====")
        print(f"[MANAGER] Query: {query}")
        
        # Step 1: Preprocess the query
        processed_query, should_continue = preprocess_query(query)
        
        # Step 2: If preprocessor handled it, return the result directly
        if not should_continue:
            print(f"[MANAGER] Preprocessor handled the request directly")
            # For async, we need to return an async generator for processed queries too
            async def _return_processed():
                yield processed_query
            return _return_processed()
        
        # Step 3: Otherwise, continue to the base agent (LLM processing)
        print(f"[MANAGER] Continuing to LLM with query: {processed_query}")
        return self._base_agent.run_async(processed_query, **kwargs)
    
    def delegate_to_sub_agent(self, agent_name: str, query: str):
        """Custom delegation method to handle manually assigned sub_agents."""
        sub_agents_map = {
            'greeting_agent': 0,
            'sales_agent': 1, 
            'purchase_agent': 2,
            'inventory_agent': 3,
            'financial_agent': 4
        }
        
        if agent_name in sub_agents_map and hasattr(self._base_agent, '_sub_agents'):
            sub_agents = self._base_agent._sub_agents
            agent_index = sub_agents_map[agent_name]
            if agent_index < len(sub_agents):
                target_agent = sub_agents[agent_index]
                print(f"[MANAGER] Delegating to {agent_name}")
                return target_agent.run(query)
        
        print(f"[MANAGER] Could not find sub-agent {agent_name}")
        return f"Could not delegate to {agent_name}"
    
    def __getattr__(self, name: str):
        """Delegate any other attributes to the base agent."""
        return getattr(self._base_agent, name)

    @property
    def sub_agents(self):
        """Access sub_agents from the base agent."""
        # Access the manually assigned sub_agents
        return getattr(self._base_agent, '_sub_agents', [])


#  ROOT AGENT DEFINITION

# ✅ Corrected root_agent creation with preprocessing wrapper
base_manager_agent = Agent(
    name="manager",
    model="gemini-2.0-flash", 
    description="Manager Orchestrator with multi-agent delegation + Gmail + Calendar tools",

    instruction="""
You are the **manager agent** (root agent). You have Gmail + Calendar powers and can generate images or charts.

 CROSS-AGENT DETECTION:
If the query involves:
- "compare" + ["sales" & "inventory", or "finance" & "purchase", etc.]
- "customer behavior" + "payment patterns"
-> First call: is_cross_agent_query(query)
-> If true -> call: handle_cross_agent_query(query)
-> If false -> continue with single-agent delegation

 DOMAIN-BASED DELEGATION:

| Keywords                                                                 | Delegate to        |
| ------------------------------------------------------------------------ | ------------------ |
| "sales", "invoice", "top customers"                                     | sales_agent        |
| "purchase", "supplier", "vendor", "orders"                              | purchase_agent     |
| "stock", "inventory", "items", "restock"                                | inventory_agent    |
| "profit", "loss", "revenue", "balance", "income", "expenses"            | financial_agent    |
| "hello", "hi", "introduce", "greetings"                                 | greeting_agent     |
| Unrecognized or fallback queries                                        | greeting_agent     |

 CRITICAL: Always capture analytics responses for email functionality!

 WORKFLOW:
1. Is it a cross-agent query? -> handle_cross_agent_query()
2. Otherwise -> Delegate to correct sub-agent
3. Capture analytics responses with format_and_store_agent_response()

Note: Email and calendar requests are handled by the preprocessor before reaching this agent.
To view recent emails, call smart_read_last_emails(count=3) which returns the latest messages from your inbox.
Use smart_generate_image(prompt) to create simple DALL·E-style images or graphs.
""",
    tools=[
        FunctionTool(handle_cross_agent_query),
        FunctionTool(is_cross_agent_query),
        FunctionTool(smart_send_email),
        FunctionTool(smart_delete_last_email),
        FunctionTool(smart_read_last_emails),
        FunctionTool(smart_schedule_event),
        FunctionTool(smart_generate_image),
        FunctionTool(format_and_store_agent_response),
    ],
    sub_agents=[],  # Empty to avoid parent conflicts - will be set manually
)

# ✅ Manually assign sub_agents to avoid parent conflicts
base_manager_agent._sub_agents = [greeting_agent, sales_agent, purchase_agent, inventory_agent, financial_agent]

# ✅ Wrap it with preprocessor-aware manager
root_agent = ManagerAgentWithPreprocessor(base_manager_agent)

manager_agent = root_agent
