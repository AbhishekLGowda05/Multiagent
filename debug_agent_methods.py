#!/usr/bin/env python3
"""
Debug script to check ADK Agent methods
"""
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("🔍 Checking ADK Agent methods...")

try:
    from DB_analysis.manager.agent import base_manager_agent
    print(f"✅ Base agent imported: {type(base_manager_agent)}")
    print(f"📋 Available methods: {[m for m in dir(base_manager_agent) if not m.startswith('_')]}")
    
    # Check if it has a different method for running
    if hasattr(base_manager_agent, 'invoke'):
        print("✅ Found 'invoke' method")
    if hasattr(base_manager_agent, 'execute'):
        print("✅ Found 'execute' method")
    if hasattr(base_manager_agent, 'run'):
        print("✅ Found 'run' method")
    if hasattr(base_manager_agent, '__call__'):
        print("✅ Found '__call__' method (callable)")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
