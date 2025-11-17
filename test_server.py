#!/usr/bin/env python3
"""Quick test to start server and check if it works"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'blog-launchpad'))

try:
    from app import app
    print("✅ App imported successfully")
    print(f"App type: {type(app)}")
    
    # Test if we can get a route
    with app.test_client() as client:
        response = client.get('/launchpad/health')
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server routes working")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"Response: {response.data[:200]}")
            
        # Test preview route
        response2 = client.get('/header/posts/82/preview?year=2025&week=45')
        print(f"Preview route status: {response2.status_code}")
        if response2.status_code != 200:
            print(f"Preview error: {response2.data[:500]}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()







