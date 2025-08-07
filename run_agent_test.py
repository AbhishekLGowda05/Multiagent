#!/usr/bin/env python3
"""
Test script to run the agent programmatically and bypass YAML config issues.
"""
import asyncio
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("✅ Starting agent test...")
print(f"📂 Project root: {project_root}")
print(f"🐍 Python path: {sys.path[:3]}...")  # Show first 3 entries

try:
    # Import the root agent
    print("📥 Importing agent from DB_analysis.manager.agent...")
    from DB_analysis.manager.agent import root_agent
    print("✅ Agent imported successfully!")
    
    async def test_agent():
        """Test the agent with a simple query"""
        query = "give me the sales summary"
        print(f"\n🚀 Testing query: '{query}'")
        print("-" * 50)
        
        try:
            # Run the agent using the async method (directly get the generator)
            response_generator = root_agent.run_async(query)
            
            # Collect the response
            final_response = ""
            async for chunk in response_generator:
                if isinstance(chunk, str):
                    final_response += chunk
                    print(f"📝 Chunk: {chunk[:100]}...")
                else:
                    print(f"🔧 Tool call: {type(chunk)}")
            
            print("\n" + "="*50)
            print("✅ FINAL RESPONSE:")
            print("="*50)
            print(final_response)
            print("="*50)
            
        except Exception as e:
            print(f"❌ Error during agent execution: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    print("\n🎯 Running async agent test...")
    asyncio.run(test_agent())
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n🔍 Checking what's available in DB_analysis...")
    
    try:
        import DB_analysis
        print(f"✅ DB_analysis module found at: {DB_analysis.__file__}")
        
        import DB_analysis.manager
        print(f"✅ DB_analysis.manager found at: {DB_analysis.manager.__file__}")
        
        # List what's in the manager module
        print(f"📋 Contents of manager module: {dir(DB_analysis.manager)}")
        
    except Exception as debug_e:
        print(f"❌ Debug import failed: {debug_e}")
        
except Exception as e:
    print(f"❌ General error: {e}")
    import traceback
    traceback.print_exc()
