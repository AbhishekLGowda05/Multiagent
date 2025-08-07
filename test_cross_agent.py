#!/usr/bin/env python3
"""
Test script for cross-agent orchestrator functionality
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Applications/Projects/Int-Assignment /DB_analysis')

from manager.agent import handle_cross_agent_query, is_cross_agent_query

def test_cross_agent_detection():
    """Test if cross-agent query detection works."""
    print("🧪 Testing Cross-Agent Query Detection")
    print("=" * 50)
    
    test_queries = [
        "Compare our top customers by sales volume with their payment patterns",
        "What are the sales trends vs inventory levels?",
        "Get me the financial summary",  # Single agent
        "Show inventory levels",  # Single agent  
        "Revenue trends and purchase patterns analysis",
        "Customer behavior and financial impact study",
        "Sales performance and inventory management report"
    ]
    
    for query in test_queries:
        is_cross = is_cross_agent_query(query)
        print(f"Query: {query}")
        print(f"Cross-agent needed: {is_cross}")
        print("-" * 30)

def test_cross_agent_execution():
    """Test cross-agent orchestrator execution."""
    print("\n🧪 Testing Cross-Agent Orchestrator Execution")
    print("=" * 50)
    
    test_query = "Compare our top customers by sales volume with their payment patterns"
    print(f"Executing: {test_query}")
    
    try:
        result = handle_cross_agent_query(test_query)
        print(f"\nResult: {result}")
        print("✅ Cross-agent orchestrator executed successfully")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_cross_agent_detection()
    test_cross_agent_execution()
