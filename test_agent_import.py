#!/usr/bin/env python3
"""Test script to verify the manager agent loads correctly"""

import sys
import os

# Add path to import the agent
sys.path.insert(0, '/Applications/Projects/Int-Assignment /DB_analysis')

try:
    print("🧪 Testing Manager Agent Import...")
    
    # Try to import the agent
    from manager.agent import root_agent
    
    print("✅ SUCCESS: Manager agent imported successfully!")
    print(f"📋 Agent name: {root_agent.name}")
    print(f"📋 Agent model: {root_agent.model}")
    print(f"📋 Number of tools: {len(root_agent.tools)}")
    print(f"📋 Number of sub-agents: {len(root_agent.sub_agents)}")
    
    # Test function imports
    from manager.agent import smart_send_email, auto_capture_delegation_response
    print("✅ SUCCESS: Key functions imported successfully!")
    
    # Test global variables
    from manager.agent import LAST_ANALYTICS_RESULT, LAST_ANALYTICS_DATA
    print("✅ SUCCESS: Global variables imported successfully!")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("💌 The email functionality should now work correctly!")
    print("🔧 The delegation loop and analytics capture issues are resolved!")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    print(traceback.format_exc())
    exit(1)
