#!/usr/bin/env python3
"""
Test Email Processing Functionality
"""

import requests
import json

def test_email_processing():
    """Test the email processing Cloud Function."""
    
    function_url = "https://us-central1-vertigo-466116.cloudfunctions.net/email-processor-v2"
    
    # Test 1: Check connection
    print("🔍 Testing Cloud Function Connection...")
    response = requests.post(function_url, json={"action": "test_connection"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()
    
    # Test 2: Process unread emails
    print("📧 Testing Email Processing...")
    response = requests.post(function_url, json={"action": "process_emails"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()
    
    # Test 3: Check specific email commands
    print("📝 Testing Email Commands...")
    test_commands = [
        {"action": "test_command", "subject": "Vertigo: Help"},
        {"action": "test_command", "subject": "Vertigo: List this week"},
        {"action": "test_command", "subject": "Vertigo: Total stats"}
    ]
    
    for cmd in test_commands:
        response = requests.post(function_url, json=cmd)
        print(f"Command: {cmd['subject']}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print()

if __name__ == "__main__":
    test_email_processing() 