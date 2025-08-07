#!/usr/bin/env python3
"""
Quick test script to verify agent delegation is working properly
"""
import sys
import os
sys.path.append('DB_analysis')

def test_cross_agent_detection():
    """Test cross-agent query detection"""
    print("🔍 Testing Cross-Agent Query Detection...")
    
    from manager.agent import is_cross_agent_query
    
    test_queries = [
        ("compare the sales of Samsung A34 in the month of September with the overall profits made in that month", True),
        ("get me the sales summary", False),
        ("compare sales with payment patterns", True),
        ("show inventory levels", False),
        ("sales vs profits", True),
        ("hello", False)
    ]
    
    for query, expected in test_queries:
        result = is_cross_agent_query(query)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{query}' -> {result} (expected: {expected})")
    
    print()

def test_root_agent_configuration():
    """Test root agent configuration"""
    print("🔧 Testing Root Agent Configuration...")
    
    from manager.agent import root_agent
    
    print(f"  ✅ Agent name: {root_agent.name}")
    print(f"  ✅ Tools count: {len(root_agent.tools)}")
    print(f"  ✅ Sub-agents count: {len(root_agent.sub_agents)}")
    
    tool_names = [tool.name for tool in root_agent.tools]
    print(f"  ✅ Tools: {tool_names}")
    
    sub_agent_names = [agent.name for agent in root_agent.sub_agents]
    print(f"  ✅ Sub-agents: {sub_agent_names}")
    
    print()

def test_sub_agent_tools():
    """Test sub-agent tools are working"""
    print("🔧 Testing Sub-Agent Tools...")
    
    from manager.sub_agents.sales_agent.agent import get_sales_summary
    from manager.sub_agents.financial_agent.agent import get_financial_summary
    
    # Test sales tool
    try:
        result = get_sales_summary("test query")
        print(f"  ✅ Sales tool working: {type(result)}")
    except Exception as e:
        print(f"  ❌ Sales tool error: {e}")
    
    # Test financial tool  
    try:
        result = get_financial_summary("test query")
        print(f"  ✅ Financial tool working: {type(result)}")
    except Exception as e:
        print(f"  ❌ Financial tool error: {e}")
    
    print()

def test_agent_query():
    """Test actual agent query execution"""
    print("🚀 Testing Agent Query Execution...")
    
    try:
        from manager.agent import root_agent
        
        # Test a simple greeting first
        print("  Testing greeting query...")
        response = root_agent.run("hello")
        print(f"  ✅ Greeting response received: {len(str(response))} chars")
        
        # Test a sales query
        print("  Testing sales query...")
        response = root_agent.run("get me the sales summary")
        print(f"  ✅ Sales response received: {len(str(response))} chars")
        print(f"  📝 Response preview: {str(response)[:200]}...")
        
    except Exception as e:
        print(f"  ❌ Agent query error: {e}")
        import traceback
        traceback.print_exc()
    
    print()

if __name__ == "__main__":
    print("🧪 AGENT DELEGATION TEST SUITE")
    print("=" * 50)
    
    test_cross_agent_detection()
    test_root_agent_configuration()
    test_sub_agent_tools()
    test_agent_query()
    
    print("=" * 50)
    print("✅ Test suite completed!")
