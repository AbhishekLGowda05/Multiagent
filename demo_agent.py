#!/usr/bin/env python3
"""
Simple agent test for demonstration purposes
"""
import sys
import asyncio
sys.path.append('DB_analysis')

async def test_agent_delegation():
    """Test agent delegation with real queries"""
    print("🚀 AGENT DELEGATION DEMONSTRATION")
    print("=" * 50)
    
    from manager.agent import root_agent, is_cross_agent_query
    
    # Test queries for demonstration
    test_queries = [
        "hello",  # Should go to greeting_agent
        "get me the sales summary",  # Should go to sales_agent  
        "compare the sales of Samsung A34 in the month of September with the overall profits made in that month",  # Should use cross-agent
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: '{query}'")
        print("-" * 40)
        
        # Check if it's a cross-agent query
        is_cross = is_cross_agent_query(query)
        print(f"Cross-agent query: {is_cross}")
        
        try:
            # Run the query
            response_stream = root_agent.run_live(query)
            
            print("📝 Response:")
            full_response = ""
            async for response in response_stream:
                print(response, end="", flush=True)
                full_response += response
            
            print(f"\n✅ Response length: {len(full_response)} characters")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 40)
    
    print("\n✅ Demonstration completed!")

if __name__ == "__main__":
    asyncio.run(test_agent_delegation())
