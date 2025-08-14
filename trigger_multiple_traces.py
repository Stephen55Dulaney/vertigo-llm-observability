#!/usr/bin/env python3
"""
Trigger multiple cloud function calls to generate different types of Langfuse traces.
"""

import requests
import json
import time
from datetime import datetime

def trigger_email_processing():
    """Trigger email processing multiple times to generate traces."""
    
    function_url = "https://us-central1-vertigo-466116.cloudfunctions.net/email-processor-v2"
    
    print("🚀 Triggering multiple email processing operations...")
    print(f"📡 Function URL: {function_url}")
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    print()
    
    trace_ids = []
    
    # Test 1: Basic email processing
    print("📧 Test 1: Basic email processing")
    try:
        response = requests.post(function_url, json={}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            trace_id = result.get('trace_id')
            if trace_id:
                print(f"✅ Created trace: {trace_id}")
                trace_ids.append(trace_id)
            print(f"📊 Processed {result.get('processed_count', 0)} emails")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n⏱️  Waiting 3 seconds...\n")
    time.sleep(3)
    
    # Test 2: Daily summary generation
    print("📝 Test 2: Daily summary generation")
    try:
        response = requests.post(
            function_url,
            json={
                "action": "generate_daily_summary",
                "recipient": "sdulaney@mergeworld.com"
            },
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Daily summary sent: {result.get('message_id', 'N/A')}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n⏱️  Waiting 3 seconds...\n")
    time.sleep(3)
    
    # Test 3: Another email processing call
    print("📧 Test 3: Second email processing call")
    try:
        response = requests.post(function_url, json={}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            trace_id = result.get('trace_id')
            if trace_id:
                print(f"✅ Created trace: {trace_id}")
                trace_ids.append(trace_id)
            print(f"📊 Processed {result.get('processed_count', 0)} emails")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Summary:")
    print(f"   Generated {len(trace_ids)} email processing traces")
    print(f"   Generated traces with IDs: {trace_ids}")
    print()
    print("📈 Check your Langfuse dashboard:")
    print("   https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")
    print()
    print("🔍 Expected trace types:")
    print("   - 'email_processor_v2' entries (function entry points)")
    print("   - 'email_processing_batch' traces (email batch processing)")
    print("   - Various span operations within each trace")
    
    return trace_ids

def test_other_cloud_functions():
    """Test other cloud functions to generate additional traces."""
    
    print("\n📡 Testing other cloud functions for additional traces...")
    
    # Test meeting processor
    meeting_url = "https://us-central1-vertigo-466116.cloudfunctions.net/meeting-processor-v2"
    print(f"\n📝 Testing meeting processor: {meeting_url}")
    
    try:
        test_payload = {
            "transcript": "This is a test meeting transcript for Langfuse trace generation. We discussed the implementation of observability tools and decided to move forward with the current approach.",
            "transcript_type": "dictation",
            "project": "vertigo",
            "participants": ["Stephen", "AI Assistant"],
            "duration_minutes": 15,
            "meeting_title": "Langfuse Integration Test Meeting"
        }
        
        response = requests.post(meeting_url, json=test_payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Meeting processing successful")
            print(f"📝 Generated notes: {len(result.get('processed_notes', ''))} characters")
        else:
            print(f"❌ Meeting processor failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Meeting processor error: {e}")

if __name__ == "__main__":
    print("🎯 Generating Multiple Langfuse Traces")
    print("=" * 60)
    
    # Generate email processing traces
    email_trace_ids = trigger_email_processing()
    
    # Test other functions  
    test_other_cloud_functions()
    
    print("\n" + "=" * 60)
    print("✅ Trace generation complete!")
    print(f"📊 Total email traces generated: {len(email_trace_ids)}")
    print("\n🌐 View all traces in Langfuse:")
    print("   https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")