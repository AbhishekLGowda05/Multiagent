print("Testing basic import...")
try:
    from manager.agent import capture_analytics_after_response
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
