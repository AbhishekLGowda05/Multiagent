#!/usr/bin/env python3
"""
Debug script to test the sales summary formatting and email sending
"""

import re
import json
from datetime import datetime

# Simulate the JSON response you received
json_response = {
    "get_sales_summary_response": {
        "result": {
            "top_customers": [
                ["BUDHAL CELL WORLD BCW", 25], 
                ["RAVI ELECTRONICS", 10], 
                ["SAHANA CELLULAR", 9], 
                ["MEGA MOBILES", 7], 
                ["GOWRI CELL POINT", 6]
            ], 
            "total_invoices": 100, 
            "voucher_types": [["GST Sales", 100]]
        }
    }
}

def format_sales_json_to_readable(json_response):
    """Convert the JSON sales response to a readable format"""
    try:
        # Extract the actual result data
        if isinstance(json_response, dict) and "get_sales_summary_response" in json_response:
            result = json_response["get_sales_summary_response"]["result"]
        elif isinstance(json_response, dict) and "result" in json_response:
            result = json_response["result"]
        else:
            result = json_response
            
        # Format top customers
        top_customers_text = "Top Customers:\n\n"
        if "top_customers" in result:
            for customer_data in result["top_customers"]:
                customer_name = customer_data[0]
                invoice_count = customer_data[1]
                top_customers_text += f"{customer_name}: {invoice_count}\n"
        
        # Add total invoices
        total_invoices = result.get("total_invoices", 0)
        
        # Add voucher types
        voucher_info = ""
        if "voucher_types" in result:
            voucher_types = result["voucher_types"][0] if result["voucher_types"] else ["Unknown", 0]
            voucher_info = f"Voucher Types: {voucher_types[0]} ({voucher_types[1]})"
        
        formatted_response = f"""📊 SALES SUMMARY REPORT
===============================

{top_customers_text}
Total Invoices: {total_invoices} 
{voucher_info}

=====================================
Report generated successfully ✅
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return formatted_response
        
    except Exception as e:
        return f"Error formatting sales data: {e}"

def extract_analytics_data_from_json(json_response):
    """Extract analytics data for chart generation"""
    try:
        if isinstance(json_response, dict) and "get_sales_summary_response" in json_response:
            result = json_response["get_sales_summary_response"]["result"]
        elif isinstance(json_response, dict) and "result" in json_response:
            result = json_response["result"]
        else:
            result = json_response
            
        analytics_data = {}
        
        if "top_customers" in result:
            top_customers = {}
            for customer_data in result["top_customers"]:
                customer_name = customer_data[0]
                invoice_count = customer_data[1]
                top_customers[customer_name] = invoice_count
            analytics_data["top_customers"] = top_customers
            
        return analytics_data
        
    except Exception as e:
        print(f"Error extracting analytics data: {e}")
        return {}

def test_email_extraction(query):
    """Test the email extraction logic"""
    print(f"\\nTesting email extraction for: {query}")
    
    pattern1 = re.search(r"(?:send|mail) (?:this|these|mail|email) to ([\\w.+-@\\s,]+)", query, re.I)
    pattern2 = re.search(r"send (?:an )?email to ([\\w.+-@\\s,]+)", query, re.I)
    pattern3 = re.search(r"([\\w.+-]+@[\\w.-]+\\.\\w+)", query, re.I)
    
    if pattern1:
        email_text = pattern1.group(1)
        subject = "Business Analysis Results"
        print(f"✅ Pattern 1 matched - Email text: {email_text}")
    elif pattern2:
        email_text = pattern2.group(1)
        subject = "Business Report"
        print(f"✅ Pattern 2 matched - Email text: {email_text}")
    elif pattern3:
        email_text = query
        subject = "Analytics Report"
        print(f"✅ Pattern 3 matched - Using entire query")
    else:
        email_text = query
        subject = "Analytics Report"
        print(f"⚠️  No pattern matched - Using entire query")
        
    # Extract email addresses
    email_pattern = r"([\\w.+-]+@[\\w.-]+\\.\\w+)"
    email_addresses = re.findall(email_pattern, email_text)
    
    print(f"📧 Extracted emails: {email_addresses}")
    print(f"📋 Subject would be: {subject}")
    
    return email_addresses, subject

def main():
    """Main test function"""
    print("🔧 DEBUGGING SALES SUMMARY AND EMAIL ISSUES")
    print("=" * 50)
    
    print("\\n1. Testing JSON Response Formatting")
    print("-" * 35)
    
    # Test converting JSON to readable format
    formatted_response = format_sales_json_to_readable(json_response)
    print("Formatted Response:")
    print(formatted_response)
    
    print("\\n2. Testing Analytics Data Extraction")
    print("-" * 38)
    
    # Test extracting analytics data for charts
    analytics_data = extract_analytics_data_from_json(json_response)
    print(f"Analytics Data: {analytics_data}")
    
    print("\\n3. Testing Email Extraction")
    print("-" * 28)
    
    # Test email extraction
    email_query = "send this mail to abhisheklgowda05@gmail.com"
    email_addresses, subject = test_email_extraction(email_query)
    
    print("\\n4. Integration Test")
    print("-" * 20)
    
    if email_addresses and analytics_data:
        print("✅ All components working:")
        print(f"   • Sales data formatted: {len(formatted_response)} characters")
        print(f"   • Analytics data extracted: {len(analytics_data)} data points")
        print(f"   • Email addresses found: {email_addresses}")
        print(f"   • Ready to send email with subject: {subject}")
        
        print("\\n📋 EMAIL CONTENT PREVIEW:")
        print("-" * 25)
        print(f"To: {', '.join(email_addresses)}")
        print(f"Subject: {subject}")
        print("Body:")
        print(formatted_response[:200] + "..." if len(formatted_response) > 200 else formatted_response)
        
    else:
        print("❌ Issues detected:")
        if not email_addresses:
            print("   • No email addresses extracted")
        if not analytics_data:
            print("   • No analytics data extracted")
    
    print("\\n🎯 SOLUTION")
    print("-" * 12)
    print("The issue is that the JSON response needs to be processed by")
    print("capture_analytics_after_response() to format it properly.")
    print("\\nThe agent should:")
    print("1. Get JSON response from sales_agent")
    print("2. Call capture_analytics_after_response(query, json_response)")
    print("3. This will format the JSON into readable text")
    print("4. Then smart_send_email() will work properly")

if __name__ == "__main__":
    main()
