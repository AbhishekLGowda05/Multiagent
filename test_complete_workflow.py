#!/usr/bin/env python3
"""
Test the complete flow: JSON response -> formatting -> email extraction
"""

import re
import json
from datetime import datetime

# Simulate the exact JSON response you received
json_response_str = '{"get_sales_summary_response": {"result": {"top_customers": [["BUDHAL CELL WORLD BCW", 25], ["RAVI ELECTRONICS", 10], ["SAHANA CELLULAR", 9], ["MEGA MOBILES", 7], ["GOWRI CELL POINT", 6]], "total_invoices": 100, "voucher_types": [["GST Sales", 100]]}}}'

def format_json_response(response_str):
    """Simulate the enhanced format_and_store_agent_response function"""
    print("[DEBUG] Processing JSON response...")
    
    analytics_data = {}
    
    try:
        json_data = json.loads(response_str)
        result_data = json_data["get_sales_summary_response"]["result"]
        
        print(f"[DEBUG] Parsing JSON sales data: {result_data}")
        
        # Format top customers from JSON
        formatted_response = "📊 SALES SUMMARY REPORT\n===============================\n\nTop Customers:\n\n"
        
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
        
        formatted_response += f"\n\n=====================================\nReport generated successfully ✅\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print(f"[DEBUG] Formatted JSON response into readable format")
        return formatted_response, analytics_data
        
    except Exception as e:
        print(f"[ERROR] JSON parsing failed: {e}")
        return response_str, {}

def test_email_extraction(query):
    """Test the updated email extraction patterns"""
    print(f"[DEBUG] Testing email extraction for: {query}")
    
    pattern1 = re.search(r"(?:send|mail) (?:this|these|mail|email) to ([\w.+-@\s,]+)", query, re.I)
    pattern2 = re.search(r"send (?:an )?email to ([\w.+-@\s,]+)", query, re.I)
    pattern3 = re.search(r"send this mail to ([\w.+-@\s,]+)", query, re.I)  # New pattern
    pattern4 = re.search(r"([\w.+-]+@[\w.-]+\.\w+)", query, re.I)
    
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
        print(f"[DEBUG] No pattern matched - Using entire query")
        
    # Extract email addresses
    email_pattern = r"([\w.+-]+@[\w.-]+\.\w+)"
    email_addresses = re.findall(email_pattern, email_text)
    
    return email_addresses, subject

def main():
    """Test the complete workflow"""
    print("🧪 TESTING COMPLETE WORKFLOW")
    print("=" * 35)
    
    print("\n1. Step 1: Format JSON Response")
    print("-" * 32)
    formatted_text, analytics_data = format_json_response(json_response_str)
    print("✅ JSON formatted successfully")
    print(f"Analytics data points: {len(analytics_data.get('top_customers', {}))}")
    
    print("\n2. Step 2: Test Email Extraction")
    print("-" * 33)
    email_query = "send this mail to abhisheklgowda05@gmail.com"
    email_addresses, subject = test_email_extraction(email_query)
    
    if email_addresses:
        print(f"✅ Email extraction successful: {email_addresses}")
        print(f"📋 Subject: {subject}")
    else:
        print("❌ Email extraction failed")
        
    print("\n3. Step 3: Integration Check")
    print("-" * 28)
    
    if email_addresses and analytics_data:
        print("🎉 COMPLETE SUCCESS!")
        print(f"   ✅ Sales data formatted: {len(formatted_text)} characters")
        print(f"   ✅ Analytics data ready: {len(analytics_data)} datasets")
        print(f"   ✅ Email addresses found: {len(email_addresses)}")
        
        print("\n📧 READY TO SEND EMAIL:")
        print(f"   To: {', '.join(email_addresses)}")
        print(f"   Subject: {subject}")
        print(f"   Body preview: {formatted_text[:150]}...")
        print(f"   Chart data: {list(analytics_data.keys())}")
        
        print("\n🔧 FIXES APPLIED:")
        print("   ✅ Added 'send this mail to' pattern")
        print("   ✅ Enhanced JSON response processing")
        print("   ✅ Improved analytics data extraction")
        print("   ✅ Email extraction now working")
        
    else:
        print("❌ Issues still present:")
        if not email_addresses:
            print("   • Email extraction failed")
        if not analytics_data:
            print("   • Analytics data extraction failed")

if __name__ == "__main__":
    main()
