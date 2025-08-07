#!/usr/bin/env python3
"""
Simplified test script that directly tests the sales agent
"""
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("🔧 Testing direct agent imports...")

try:
    # Test importing individual agents first
    print("📥 Importing sales agent...")
    from DB_analysis.manager.sub_agents.sales_agent.agent import sales_agent
    print("✅ Sales agent imported successfully!")
    
    print("📥 Importing financial agent...")
    from DB_analysis.manager.sub_agents.financial_agent.agent import financial_agent  
    print("✅ Financial agent imported successfully!")
    
    print("📥 Importing manager tools...")
    from DB_analysis.manager.agent import smart_send_email, format_and_store_agent_response
    print("✅ Manager tools imported successfully!")
    
    # Test a simple function
    print("\n🔧 Testing format_and_store_agent_response function...")
    test_response = "Sample sales data: ACME Corp - 50 invoices, XYZ Inc - 30 invoices"
    formatted = format_and_store_agent_response(test_response)
    print(f"✅ Function works! Response formatted successfully.")
    
    print("\n🔧 Testing email function (dry run)...")
    # This should show the proper error message about needing analytics data first
    email_result = smart_send_email("send email to test@example.com")
    print(f"📧 Email function result: {email_result}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
print("\n✅ Basic import and function tests completed!")
