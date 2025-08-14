#!/usr/bin/env python3
"""
Test the 5:30 PM end-of-day summary functionality.
"""

import requests
import json

def test_eod_summary():
    """Test the 5:30 PM end-of-day summary by calling the email processor directly."""
    
    url = "https://us-central1-vertigo-466116.cloudfunctions.net/email-processor-v2"
    
    payload = {
        "action": "generate_daily_summary",
        "recipient": "sdulaney@mergeworld.com",
        "summary_type": "end_of_day"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("🚀 Testing 5:30 PM End-of-Day Summary Generation")
        print("=" * 60)
        print(f"URL: {url}")
        print(f"Recipient: {payload['recipient']}")
        print()
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Success! End-of-day summary should have been sent.")
            print("Check your email at sdulaney@mergeworld.com")
        else:
            print(f"\n❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing end-of-day summary: {e}")

def test_eod_scheduler_job():
    """Test the end-of-day scheduler job manually."""
    
    import subprocess
    
    try:
        print("🕐 Testing End-of-Day Scheduler Job")
        print("=" * 60)
        
        result = subprocess.run(
            ["gcloud", "scheduler", "jobs", "run", "daily-summary-530pm", "--location=us-central1"],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✅ Scheduler job executed successfully!")
        print("Check your email at sdulaney@mergeworld.com")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running scheduler job: {e}")
        print(f"Error output: {e.stderr}")

if __name__ == "__main__":
    print("Choose a test option:")
    print("1. Test direct function call")
    print("2. Test scheduler job")
    print("3. Run both tests")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        test_eod_summary()
    elif choice == "2":
        test_eod_scheduler_job()
    elif choice == "3":
        print("\n" + "="*60)
        test_eod_summary()
        print("\n" + "="*60)
        test_eod_scheduler_job()
    else:
        print("Invalid choice. Running direct function test...")
        test_eod_summary() 