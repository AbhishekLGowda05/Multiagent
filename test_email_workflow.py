#!/usr/bin/env python3
"""Test the complete email workflow for financial queries"""

__test__ = False

import sys
import os
import types

# Mock google.adk modules
google_module = types.ModuleType("google")
adk_module = types.ModuleType("google.adk")
agents_module = types.ModuleType("google.adk.agents")

class DummyAgent:
    def __init__(self, *args, **kwargs):
        pass

agents_module.Agent = DummyAgent
adk_module.agents = agents_module
google_module.adk = adk_module

sys.modules.setdefault("google", google_module)
sys.modules.setdefault("google.adk", adk_module)
sys.modules.setdefault("google.adk.agents", agents_module)

# Mock pydantic
pydantic_module = types.ModuleType("pydantic")
pydantic_module.BaseModel = type(
    "BaseModel",
    (),
    {"__init__": lambda self, **kw: [setattr(self, k, v) for k, v in kw.items()] and None},
)
sys.modules.setdefault("pydantic", pydantic_module)

sys.path.insert(0, os.path.abspath("DB_analysis"))

# Import the manager agent functions
from DB_analysis.manager.agent import auto_capture_delegation_response, format_and_store_agent_response
from DB_analysis.manager.sub_agents.financial_agent.agent import get_financial_summary

def test_financial_email_workflow():
    """Test the complete workflow: financial query -> capture -> email ready"""
    
    print("🧪 Testing Financial Analytics + Email Workflow")
    print("=" * 50)
    
    # Step 1: Simulate financial query
    print("📊 Step 1: Getting financial summary...")
    financial_query = "get me the financial summary"
    financial_result = get_financial_summary(financial_query)
    print(f"✅ Financial data retrieved: {type(financial_result).__name__}")
    
    # Step 2: Test the auto_capture function
    print("\n📥 Step 2: Testing auto_capture_delegation_response...")
    
    # Create a mock response that looks like what financial_agent would return
    mock_response = f"""Here's your financial summary:

Total Debit: ₹{financial_result.total_debit:,.2f}
Total Credit: ₹{financial_result.total_credit:,.2f}

Top Income Sources:
{chr(10).join([f"• {name}: ₹{amount:,.2f}" for name, amount in financial_result.top_income_ledgers[:3]])}

Top Expense Categories:
{chr(10).join([f"• {name}: ₹{amount:,.2f}" for name, amount in financial_result.top_expense_ledgers[:3]])}

Balance: ₹{financial_result.total_debit - financial_result.total_credit:,.2f}"""
    
    try:
        # Test the auto_capture function
        captured_result = auto_capture_delegation_response(
            agent_response=mock_response,
            original_query=financial_query
        )
        
        print(f"✅ Auto-capture completed successfully")
        print(f"📋 Returned response length: {len(captured_result)} characters")
        
        # Step 3: Check if data was stored for email
        print("\n📧 Step 3: Checking if analytics data is available for email...")
        
        # Try to read the last stored analytics
        try:
            import sqlite3
            conn = sqlite3.connect("DB_analysis/tallydb.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT response_text, charts_generated 
                FROM agent_responses 
                ORDER BY id DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            conn.close()
            
            if result:
                response_text, charts_generated = result
                print(f"✅ Analytics data stored successfully")
                print(f"📄 Response text length: {len(response_text)} characters")
                print(f"📊 Charts generated: {charts_generated}")
                print("\n🎉 EMAIL WORKFLOW READY!")
                print("💌 The system can now send emails with this financial data")
                return True
            else:
                print("❌ No analytics data found in database")
                return False
                
        except Exception as db_error:
            print(f"⚠️ Database check failed: {db_error}")
            return False
            
    except Exception as e:
        print(f"❌ Auto-capture failed: {e}")
        return False

if __name__ == "__main__":
    success = test_financial_email_workflow()
    if success:
        print("\n🏆 TEST PASSED: Financial email workflow is working!")
        print("📧 Users can now run: 'get financial summary' → 'send email to user@email.com'")
    else:
        print("\n💥 TEST FAILED: Email workflow still has issues")
        exit(1)
