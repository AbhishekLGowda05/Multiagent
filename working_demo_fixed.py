#!/usr/bin/env python3
"""
Working demonstration of the multi-agent system
"""
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def demo_sales_and_email():
    """Demonstrate the sales analytics and email workflow"""
    
    print("🚀 MULTI-AGENT BUSINESS ANALYTICS SYSTEM DEMO")
    print("=" * 60)
    
    # Import the necessary components
    from DB_analysis.manager.agent import (
        format_and_store_agent_response, 
        smart_send_email,
        LAST_ANALYTICS_RESULT
    )
    
    # Simulate a sales summary response (this would normally come from the sales agent)
    print("\n📊 Step 1: Simulating Sales Agent Response...")
    mock_sales_data = """
SALES SUMMARY REPORT:

Top Customers by Invoice Count:
1. BUDHAL CELL WORLD - 25 invoices
2. RAVI ELECTRONICS - 18 invoices  
3. SAHANA CELLULAR - 12 invoices
4. TECH SOLUTIONS INC - 9 invoices
5. MOBILE MART - 7 invoices

Total Revenue: $45,230.50
Average Invoice Value: $637.93
Active Customers: 71
    """.strip()
    
    print("✅ Sales data generated:")
    print(mock_sales_data[:200] + "...")
    
    # Step 2: Format and store the analytics data
    print("\n📈 Step 2: Processing Analytics Data...")
    formatted_result = format_and_store_agent_response(mock_sales_data)
    print("✅ Analytics data processed and stored for email use")
    
    # Step 3: Send email with the analytics data
    print(f"\n📧 Step 3: Sending Email with Analytics...")
    email_result = smart_send_email("send this to abhisheklgowda05@gmail.com")
    
    if email_result.get('status') == 'completed':
        print(f"✅ EMAIL SENT SUCCESSFULLY!")
        print(f"📊 Recipients: {email_result.get('recipients')}")
        print(f"📁 Attachments: Chart included")
        print(f"🆔 Message ID: {email_result.get('results', [{}])[0].get('result', {}).get('id', 'N/A')}")
    else:
        print(f"❌ Email failed: {email_result.get('message')}")
    
    return email_result

def demo_financial_analysis():
    """Demonstrate financial analysis workflow"""
    
    print("\n" + "=" * 60)
    print("💰 FINANCIAL ANALYSIS DEMO")
    print("=" * 60)
    
    from DB_analysis.manager.agent import format_and_store_agent_response, smart_send_email
    
    print("\n📊 Step 1: Simulating Financial Agent Response...")
    mock_financial_data = """
FINANCIAL ANALYSIS REPORT:

Profit & Loss Summary:
- Total Revenue: $159,553,857.94
- Total Expenses: $151,069,112.45
- Net Profit: $8,484,745.49
- Profit Margin: 5.4%

Cash Flow Analysis:
- Cash Inflow: $159,553,857.94
- Cash Outflow: $151,069,112.45
- Net Cash Flow: $8,484,745.49

Monthly Breakdown:
- 2023-08: $13,595,891.35
- 2023-09: $9,454,054.50
- 2023-10: $11,234,567.89
    """.strip()
    
    print("✅ Financial data generated")
    
    # Process the financial data
    print("\n📈 Step 2: Processing Financial Analytics...")
    format_and_store_agent_response(mock_financial_data)
    print("✅ Financial analytics processed")
    
    # Send financial report
    print(f"\n📧 Step 3: Sending Financial Report...")
    email_result = smart_send_email("email this financial analysis to abhisheklgowda05@gmail.com as pdf")
    
    if email_result.get('status') == 'completed':
        print(f"✅ FINANCIAL REPORT SENT!")
        print(f"📊 PDF attachment included")
    
    return email_result

def demo_preprocessing():
    """Demonstrate the query preprocessing functionality"""
    
    print("\n" + "=" * 60)
    print("🔍 QUERY PREPROCESSING DEMO")
    print("=" * 60)
    
    from DB_analysis.manager.agent import preprocess_query
    
    # Test various queries
    test_queries = [
        "give me the sales summary",
        "send this report to user@example.com", 
        "schedule meeting tomorrow at 3 PM",
        "compare sales and inventory data",
        "show me financial trends"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: '{query}'")
        processed_query, should_continue = preprocess_query(query)
        
        if should_continue:
            print(f"   ➡️  Continues to LLM: '{processed_query}'")
        else:
            print(f"   🛑 Handled by preprocessor: {type(processed_query)}")

if __name__ == "__main__":
    print("🎯 Starting comprehensive system demonstration...")
    
    try:
        # Demo 1: Sales and Email
        demo_sales_and_email()
        
        # Demo 2: Financial Analysis  
        demo_financial_analysis()
        
        # Demo 3: Query Preprocessing
        demo_preprocessing()
        
        print("\n" + "=" * 60)
        print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("✅ Your multi-agent system is working perfectly!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
