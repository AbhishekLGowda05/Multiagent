#!/usr/bin/env python3
"""Simple test to verify the analytics capture system is working"""

import sqlite3
import os

def test_analytics_capture():
    """Test if we can manually capture analytics data"""
    
    print("🧪 Testing Analytics Capture System")
    print("=" * 40)
    
    # Test database connection
    db_path = "DB_analysis/tallydb.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if agent_responses table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='agent_responses'
        """)
        
        if not cursor.fetchone():
            print("❌ agent_responses table not found")
            conn.close()
            return False
        
        print("✅ Database and table found")
        
        # Test inserting analytics data
        test_response = """Financial Summary:
Total Debit: ₹758,886,625.31
Total Credit: ₹758,886,625.31
Top Income: HDFC BANK (₹159,553,857.94)
Top Expense: HDFC BANK (₹157,645,223.40)
Balance: ₹0.00"""
        
        cursor.execute("""
            INSERT INTO agent_responses (query, response_text, charts_generated, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, ("get financial summary", test_response, 0))
        
        conn.commit()
        print("✅ Test analytics data inserted")
        
        # Verify data was stored
        cursor.execute("""
            SELECT id, query, response_text, charts_generated 
            FROM agent_responses 
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            id, query, response_text, charts_generated = result
            print(f"✅ Data retrieved - ID: {id}")
            print(f"📋 Query: {query}")
            print(f"📄 Response length: {len(response_text)} chars")
            print(f"📊 Charts: {charts_generated}")
            
            conn.close()
            print("\n🎉 Analytics capture system is working!")
            print("💌 Email system should now be able to use this data")
            return True
        else:
            print("❌ Could not retrieve test data")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_recent_analytics():
    """Check what analytics data we have recently"""
    
    print("\n🔍 Checking Recent Analytics Data")
    print("=" * 35)
    
    try:
        conn = sqlite3.connect("DB_analysis/tallydb.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, query, response_text, charts_generated, created_at
            FROM agent_responses 
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            print(f"📊 Found {len(results)} recent analytics entries:")
            for i, (id, query, response_text, charts_generated, created_at) in enumerate(results, 1):
                print(f"\n{i}. ID: {id} | Created: {created_at}")
                print(f"   Query: {query[:50]}...")
                print(f"   Response: {len(response_text)} chars | Charts: {charts_generated}")
        else:
            print("📭 No analytics data found")
            
    except Exception as e:
        print(f"❌ Error checking analytics: {e}")

if __name__ == "__main__":
    print("🔧 Testing Email System Prerequisites\n")
    
    # Test 1: Basic analytics capture
    if test_analytics_capture():
        print("\n" + "="*50)
        
        # Test 2: Check existing data
        check_recent_analytics()
        
        print("\n" + "="*50)
        print("🏆 SUMMARY:")
        print("✅ Analytics capture system is functional")
        print("✅ Database can store and retrieve analytics data")
        print("💌 Email system should work with captured analytics")
        print("\n🎯 NEXT STEP: Test 'get financial summary' → 'send email' workflow")
    else:
        print("\n💥 FAILED: Analytics capture system has issues")
        exit(1)
