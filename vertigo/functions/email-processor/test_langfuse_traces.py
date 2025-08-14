#!/usr/bin/env python3
"""
Test script to verify that the email processor is generating Langfuse traces.
"""

import requests
import json
import time
from datetime import datetime

def test_cloud_function_langfuse():
    """Test the deployed cloud function to generate Langfuse traces."""
    
    # Cloud function URL
    function_url = "https://us-central1-vertigo-466116.cloudfunctions.net/email-processor-v2"
    
    print("🚀 Testing email-processor-v2 cloud function with Langfuse tracing...")
    print(f"📡 Function URL: {function_url}")
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    print()
    
    try:
        # Test 1: Basic function invocation (should process unread emails)
        print("📧 Test 1: Basic email processing (process unread emails)")
        print("Making request to cloud function...")
        
        response = requests.post(
            function_url,
            json={},  # Empty payload should trigger unread email processing
            timeout=60  # Give it time to process
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response: {json.dumps(result, indent=2)}")
            
            # Extract trace ID if available
            trace_id = result.get('trace_id')
            if trace_id:
                print(f"🔍 Trace ID: {trace_id}")
                print(f"🌐 Check Langfuse dashboard: https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print()
    print("⏱️  Waiting 5 seconds for trace processing...")
    time.sleep(5)
    
    try:
        # Test 2: Generate automatic daily summary (another trace type)
        print("📝 Test 2: Generate automatic daily summary")
        print("Making request for daily summary...")
        
        response = requests.post(
            function_url,
            json={
                "action": "generate_daily_summary",
                "recipient": "sdulaney@mergeworld.com"
            },
            timeout=60
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()
    print("🎯 Test completed!")
    print("📈 Check your Langfuse dashboard for new traces:")
    print("   https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")
    print()
    print("Expected traces:")
    print("   1. 'email_processor_v2' - Main function entry point")
    print("   2. 'email_processing_batch' - Batch processing of unread emails") 
    print("   3. 'process_individual_email' - Individual email processing spans")
    print()
    
    return True

if __name__ == "__main__":
    test_cloud_function_langfuse()