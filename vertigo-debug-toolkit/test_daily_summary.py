#!/usr/bin/env python3
"""
Test script for the new 3:00 PM daily summary feature.
"""

import os
import json
import requests
from datetime import datetime

# Sample daily content for testing
SAMPLE_DAILY_CONTENT = """
My Ambition:
Drive clarity and momentum on agentic tools (WhoKnows, Vertigo, Firebase), while helping the team accelerate real-world testing and adoption.

What We Did Today:
Worked with Lily and Sydney to refine WhoKnows prompts and deploy them as a Gemini Gem. Integrated prompt testing into Cursor. Continued Firebase Studio prototyping and confirmed fit for lightweight UI workflows.

What We'll Do Next:
Add prompt version control and branching via Langfuse. Begin security hardening for Vertigo. Sync with Kurt and Jeff to align Firebase experiments with broader architecture planning.
"""

def test_daily_summary_feature():
    """Test the daily summary feature with sample content."""
    
    print("🧪 Testing 3:00 PM Daily Summary Feature")
    print("=" * 60)
    
    # Test the meeting processor directly
    meeting_processor_url = "https://us-central1-vertigo-466116.cloudfunctions.net/meeting-processor"
    
    payload = {
        "transcript": SAMPLE_DAILY_CONTENT,
        "transcript_type": "daily_summary",
        "project": "vertigo",
        "participants": ["Stephen"],
        "duration_minutes": 0,
        "meeting_title": "3:00 PM Summary",
        "prompt_variant": "daily_summary"
    }
    
    try:
        print("📤 Sending daily summary content to meeting processor...")
        response = requests.post(meeting_processor_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Daily summary processed.")
            print("\n📊 Processed Notes:")
            print("-" * 40)
            print(result.get('processed_notes', 'No notes generated'))
            
            print("\n🔍 Structured Data:")
            print("-" * 40)
            structured_data = result.get('structured_data', {})
            if structured_data:
                for key, value in structured_data.items():
                    print(f"{key}: {value}")
            else:
                print("No structured data generated")
                
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_email_processor_simulation():
    """Simulate how the email processor would handle a daily summary request."""
    
    print("\n📧 Testing Email Processor Simulation")
    print("=" * 60)
    
    # Simulate the email processing logic
    subject = "3:00 PM Summary"
    body = SAMPLE_DAILY_CONTENT
    sender = "stephen.dulaney@gmail.com"
    
    # Test the detection functions (implemented directly)
    def is_daily_summary_request(subject, body):
        """Check if this is a 3:00 PM daily summary request."""
        daily_summary_keywords = ['3:00', '3:00 pm', '3pm', 'daily summary', 'boss update', 'daily update']
        subject_lower = subject.lower()
        body_lower = body.lower()
        
        return any(keyword in subject_lower or keyword in body_lower for keyword in daily_summary_keywords)
    
    def detect_project(subject, body):
        """Detect project from subject or body."""
        projects = ['vertigo', 'memento', 'gemino', 'merge']
        text = (subject + " " + body).lower()
        
        for project in projects:
            if project in text:
                return project
        return 'vertigo'  # Default
    
    is_daily = is_daily_summary_request(subject, body)
    project = detect_project(subject, body)
    
    print(f"📧 Subject: {subject}")
    print(f"👤 Sender: {sender}")
    print(f"🔍 Is Daily Summary Request: {is_daily}")
    print(f"📁 Detected Project: {project}")
    
    if is_daily:
        print("✅ Email would be processed as daily summary request")
    else:
        print("❌ Email would NOT be processed as daily summary request")

if __name__ == "__main__":
    print("🚀 Vertigo 3:00 PM Daily Summary Feature Test")
    print("=" * 60)
    
    # Test the meeting processor
    test_daily_summary_feature()
    
    # Test email processor simulation
    test_email_processor_simulation()
    
    print("\n" + "=" * 60)
    print("💡 Next Steps:")
    print("1. Send an email to vertigo.agent.2025@gmail.com")
    print("2. Subject: '3:00 PM Summary'")
    print("3. Body: Your actual daily activities")
    print("4. Check for auto-reply with formatted summary")
    print("=" * 60) 