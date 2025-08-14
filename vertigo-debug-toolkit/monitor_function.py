#!/usr/bin/env python3
"""
Monitor Cloud Function health and performance.
"""

import requests
import time
import json
from datetime import datetime

def check_function_health():
    """Check if Cloud Function is responding."""
    
    url = "https://us-central1-vertigo-466116.cloudfunctions.net/email_processor"
    
    try:
        # Test GET request
        response = requests.get(url, timeout=5)
        print(f"✅ Function reachable: {response.status_code}")
        
        # Test POST request
        test_payload = {"message": {"data": "health_check"}}
        response = requests.post(url, json=test_payload, timeout=10)
        print(f"✅ Function processing: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Function error: {e}")
        return False

def monitor_continuously():
    """Monitor function continuously."""
    
    print("🔍 Starting continuous monitoring...")
    print("Press Ctrl+C to stop")
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] Checking function health...")
        
        if not check_function_health():
            print("⚠️  Function may be down - check logs")
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    monitor_continuously()
