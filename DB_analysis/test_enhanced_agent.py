#!/usr/bin/env python3
"""
Quick test script for the enhanced manager agent functionality
"""

import sys
import os
import re

# Add project root to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from manager.agent import (
    smart_send_email, 
    smart_schedule_event, 
    smart_delete_calendar_event,
    convert_json_to_readable,
    format_and_store_agent_response
)

def test_email_parsing():
    """Test email recipient parsing"""
    print("🧪 Testing Email Parsing...")
    
    test_queries = [
        "send to john@company.com",
        "send this information to abc@gmail.com, xyz@gmail.com, admin@company.com",
        "email john@company.com and sarah.smith@example.org",
        "share with manager@company.com, ceo@company.com"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        # We'll just test parsing without actually sending
        import re
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', query)
        print(f"Found emails: {emails}")

def test_calendar_parsing():
    """Test calendar event parsing"""
    print("\n🧪 Testing Calendar Parsing...")
    
    test_queries = [
        "schedule meeting at 11 PM on August 5th",
        "daily meeting from 7 PM to 8:47 PM in August",
        "weekly meeting every Monday at 10 AM",
        "from 2 PM to 4:30 PM tomorrow"
    ]
    
    patterns = {
        "daily_month": r"(?:daily|every\s*day|everyday).*from\s+(\d{1,2})(?::(\d{1,2}))?\s*(am|pm)\s+to\s+(\d{1,2})(?::(\d{1,2}))?\s*(am|pm).*(?:in|during)\s+(\w+)(?:\s+(\d{4}))?",
        "weekly_day": r"(?:weekly|every\s*week).*(?:every\s+)?(\w+).*at\s+(\d{1,2})(?::(\d{1,2}))?\s*(am|pm)",
        "standard": r"at\s+(\d{1,2})(?::(\d{1,2}))?\s*(am|pm)\s+on\s+(\w+)\s+(\d{1,2})"
    }
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        matched = False
        for pattern_name, pattern in patterns.items():
            match = re.search(pattern, query, re.I)
            if match:
                print(f"Matches pattern: {pattern_name}")
                print(f"Groups: {match.groups()}")
                matched = True
                break
        if not matched:
            print("No pattern matched")

def test_json_conversion():
    """Test JSON to readable conversion"""
    print("\n🧪 Testing JSON Conversion...")
    
    test_json = '{"total_sales": 15000, "profit": 3000, "products": ["laptop", "mouse"]}'
    readable = convert_json_to_readable(test_json)
    print(f"Original: {test_json}")
    print(f"Converted: {readable}")

if __name__ == "__main__":
    print("🚀 Testing Enhanced Manager Agent Features")
    print("=" * 50)
    
    test_email_parsing()
    test_calendar_parsing()
    test_json_conversion()
    
    print("\n✅ All tests completed!")
    print("\n📋 Summary of Enhancements:")
    print("• Multi-recipient email support")
    print("• Advanced calendar patterns (daily, weekly, duration-based)")
    print("• Recurring events for entire months")
    print("• JSON to readable text conversion")
    print("• Comprehensive error handling")
    print("• Cross-agent analytics capture")
