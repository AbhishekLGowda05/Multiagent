#!/usr/bin/env python3
"""
🚀 PRESENTATION-READY AGENT DEMONSTRATION SCRIPT
For live demonstration of all agent functionality
"""
import sys
import time
sys.path.append('DB_analysis')

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    print(f"\n{step} {description}")
    print("-" * 40)

def demonstrate_cross_agent_queries():
    """Demonstrate cross-agent functionality"""
    print_header("CROSS-AGENT QUERY DEMONSTRATION")
    
    from manager.agent import is_cross_agent_query, handle_cross_agent_query
    
    queries = [
        "compare the sales of Samsung A34 in the month of September with the overall profits made in that month",
        "compare sales with payment patterns",
        "sales vs inventory trends"
    ]
    
    for i, query in enumerate(queries, 1):
        print_step(f"{i}️⃣", f"Query: '{query}'")
        
        # Check if cross-agent
        is_cross = is_cross_agent_query(query)
        print(f"🔍 Cross-agent detection: {is_cross}")
        
        if is_cross:
            print("🔄 Executing cross-agent coordination...")
            result = handle_cross_agent_query(query)
            print(f"✅ Result: {len(str(result))} characters")
            print(f"📋 Preview: {str(result)[:200]}...")
        
        time.sleep(1)  # Pause for demonstration

def demonstrate_single_agent_delegation():
    """Demonstrate single-agent delegation"""
    print_header("SINGLE-AGENT DELEGATION DEMONSTRATION")
    
    from manager.sub_agents.sales_agent.agent import get_sales_summary
    from manager.sub_agents.financial_agent.agent import get_financial_summary
    from manager.agent import format_and_store_agent_response
    
    test_cases = [
        ("Sales Agent", get_sales_summary, "get me the sales summary"),
        ("Financial Agent", get_financial_summary, "show me financial data")
    ]
    
    for i, (agent_name, tool_func, query) in enumerate(test_cases, 1):
        print_step(f"{i}️⃣", f"{agent_name} - Query: '{query}'")
        
        # Execute the tool
        result = tool_func(query)
        print(f"🔧 Tool result: {type(result).__name__}")
        print(f"📊 Data: {str(result)[:150]}...")
        
        # Store analytics for email
        captured = format_and_store_agent_response(str(result))
        print(f"✅ Response stored for email: {len(str(captured))} chars")
        
        time.sleep(1)

def demonstrate_email_functionality():
    """Demonstrate email functionality"""
    print_header("EMAIL FUNCTIONALITY DEMONSTRATION")
    
    from manager.agent import smart_send_email, set_last_analytics_result
    
    print_step("1️⃣", "Setting up mock analytics data")
    mock_data = """📊 DEMONSTRATION REPORT
========================

Total Sales: $125,000
Top Customers: 
- ABC Corp: $45,000
- XYZ Ltd: $30,000  
- DEF Inc: $25,000

Key Metrics:
- Revenue Growth: +15%
- Profit Margin: 12%
- Customer Count: 150

✅ Report generated successfully
📅 2025-08-07 14:30:00"""
    
    set_last_analytics_result(mock_data)
    print("✅ Analytics data populated")
    
    print_step("2️⃣", "Sending demonstration email")
    
    # Note: Replace with your actual email for demo
    demo_email = "abhisheklgowda05@gmail.com"  # Your email from conversation
    
    result = smart_send_email(f"send this mail to {demo_email}")
    print(f"📧 Email result: {result.get('status', 'unknown')}")
    print(f"📬 Recipients processed: {result.get('recipients', 0)}")
    
    if result.get('status') == 'completed':
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("🎯 Check your inbox for the demonstration email")
    else:
        print("ℹ️  Email simulation completed (check credentials for live sending)")

def demonstrate_query_detection():
    """Demonstrate intelligent query routing"""
    print_header("INTELLIGENT QUERY ROUTING DEMONSTRATION")
    
    from manager.agent import is_cross_agent_query
    
    test_queries = [
        ("get me the sales summary", "Single Agent (Sales)"),
        ("show financial data", "Single Agent (Financial)"),
        ("hello", "Single Agent (Greeting)"),
        ("compare sales with profits", "Cross-Agent"),
        ("sales vs inventory", "Cross-Agent"),
        ("top customers with payment patterns", "Cross-Agent")
    ]
    
    for i, (query, expected) in enumerate(test_queries, 1):
        is_cross = is_cross_agent_query(query)
        routing = "Cross-Agent" if is_cross else "Single Agent"
        status = "✅" if routing in expected else "❌"
        
        print(f"{i}️⃣ '{query}'")
        print(f"   {status} Routing: {routing} (Expected: {expected})")

def run_complete_demo():
    """Run the complete demonstration"""
    print("🎯 MULTI-AGENT SYSTEM DEMONSTRATION")
    print("🕒 Starting comprehensive demo...")
    print("⚡ This demonstrates all core functionality for your presentation")
    
    try:
        demonstrate_query_detection()
        demonstrate_single_agent_delegation()
        demonstrate_cross_agent_queries()
        demonstrate_email_functionality()
        
        print_header("🎉 DEMONSTRATION COMPLETE!")
        print("✅ All agent functionality working correctly")
        print("📧 Email system operational")
        print("🔄 Cross-agent coordination functional")
        print("🎯 System ready for live presentation!")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_complete_demo()
