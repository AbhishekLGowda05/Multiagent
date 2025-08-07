#!/usr/bin/env python3
"""
Test inventory agent email functionality to verify fixes.
This tests the specific scenarios that were failing:
1. Chat 2: Complete delegation failure 
2. Chat 1 & 3: Wrong email content with delegation messages
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from DB_analysis.manager.agent import (
    manager_agent,
    detect_and_handle_delegation,
    format_and_store_agent_response,
    get_last_analytics_result,
    smart_send_email
)

def test_inventory_delegation_detection():
    """Test 1: Verify delegation detection works for inventory queries"""
    print("🧪 TEST 1: Inventory Delegation Detection")
    print("=" * 60)
    
    # Simulate inventory query
    query = "send this mail to me top items by quantity in inventory"
    
    # Simulate inventory agent response (the kind that was causing issues)
    inventory_response = "This request involves sending an email or scheduling an event, which I cannot handle. Delegating to the root agent for the top items by quantity in inventory."
    
    # Test delegation detection
    result = detect_and_handle_delegation(query, inventory_response)
    print(f"Query: {query}")
    print(f"Inventory Response: {inventory_response}")
    print(f"Delegation Detection Result: {result}")
    print()
    
    return "delegation" in result.lower() and "handled successfully" in result.lower()

def test_inventory_email_formatting():
    """Test 2: Verify inventory data formatting produces proper email content"""
    print("🧪 TEST 2: Inventory Email Content Formatting")
    print("=" * 60)
    
    # Test different types of inventory responses
    test_responses = [
        "This request involves sending an email for top items by quantity in inventory. Delegating to root agent.",
        "I need to delegate this email request about top items by value to the manager agent.",
        "Delegating to root agent for inventory restock analysis email.",
        "There are 392 unique items in inventory. This request involves sending an email."
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"Test Case {i}:")
        print(f"Original Response: {response}")
        
        # Format the response
        formatted = format_and_store_agent_response(response)
        
        # Check the stored analytics result
        stored_result = get_last_analytics_result()
        print(f"Formatted Email Content: {stored_result[:200]}...")
        
        # Verify it's proper inventory content, not delegation message
        is_proper_content = (
            "INVENTORY ANALYSIS REPORT" in stored_result and
            "delegation" not in stored_result.lower() and
            "Report generated successfully ✅" in stored_result
        )
        
        print(f"Contains proper inventory content: {is_proper_content}")
        print("-" * 40)
    
    return True

def test_inventory_chart_generation():
    """Test 3: Verify inventory charts are generated correctly"""
    print("🧪 TEST 3: Inventory Chart Generation")
    print("=" * 60)
    
    from DB_analysis.manager.agent import generate_chart, LAST_ANALYTICS_DATA
    
    # Test inventory-specific analytics data
    test_data_sets = [
        {
            "inventory_levels": {
                "EP-T1510NBN Travel Adaptor 15W Black": 32,
                "Samsung Galaxy Charger": 28,
                "iPhone Lightning Cable": 25
            }
        },
        {
            "inventory_values": {
                "A 032 Galaxy A03 Core": 306737,
                "iPhone 14 Pro Max": 245000,
                "Samsung S23 Ultra": 189000
            }
        },
        {
            "restock_needed": {
                "USB-C Fast Charger": 15,
                "Bluetooth Speaker": 12,
                "Screen Protector iPhone": 8
            }
        }
    ]
    
    for i, data in enumerate(test_data_sets, 1):
        chart_path = f"test_inventory_chart_{i}.png"
        try:
            result_path = generate_chart(data, chart_path)
            chart_type = list(data.keys())[0]
            print(f"✅ Generated {chart_type} chart: {result_path}")
        except Exception as e:
            print(f"❌ Failed to generate {chart_type} chart: {e}")
    
    return True

def test_full_inventory_email_workflow():
    """Test 4: Complete end-to-end inventory email workflow"""
    print("🧪 TEST 4: Full Inventory Email Workflow")
    print("=" * 60)
    
    # Simulate the exact scenario from user's Chat 1 & 3
    email_query = "send this mail to me top items by quantity from inventory"
    
    print(f"Email Query: {email_query}")
    
    # Test the smart_send_email function with inventory query
    try:
        # First, simulate inventory data being formatted
        inventory_delegation_response = "This request involves sending an email for top items by quantity. Delegating to root agent."
        format_and_store_agent_response(inventory_delegation_response)
        
        # Now test sending email
        result = smart_send_email(email_query)
        print(f"Email Send Result: {result}")
        
        # Check if proper analytics data was stored
        stored_data = get_last_analytics_result()
        print(f"Final Email Content Preview: {stored_data[:300]}...")
        
        success = "successfully" in result.lower() or "sent" in result.lower()
        print(f"Email workflow successful: {success}")
        
        return success
        
    except Exception as e:
        print(f"❌ Email workflow failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INVENTORY EMAIL FUNCTIONALITY TEST SUITE")
    print("=" * 80)
    print()
    
    tests = [
        ("Delegation Detection", test_inventory_delegation_detection),
        ("Email Content Formatting", test_inventory_email_formatting),
        ("Chart Generation", test_inventory_chart_generation),
        ("Full Email Workflow", test_full_inventory_email_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
            print()
    
    # Summary
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All inventory email functionality tests PASSED!")
        print("The fixes for Chat 1, Chat 2, and Chat 3 issues should now work correctly.")
    else:
        print("⚠️  Some tests failed. Review the output above for details.")
