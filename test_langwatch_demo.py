#!/usr/bin/env python3
"""
Quick Langwatch demo trace generator for CTO meeting.
"""

import os
import sys
import requests
import json
from datetime import datetime

# Set environment variables from .env file
sys.path.append('vertigo-debug-toolkit')
from dotenv import load_dotenv
load_dotenv('vertigo-debug-toolkit/.env')

def create_langwatch_trace():
    """Create a demo trace in Langwatch."""
    api_key = os.getenv('LANGWATCH_API_KEY')
    if not api_key:
        print("❌ LANGWATCH_API_KEY not found in environment")
        return False
    
    print(f"🔑 Using Langwatch API key: {api_key[:20]}...")
    
    # Demo trace data
    trace_data = {
        "project_id": "eunoia-Eyh6Gz",
        "trace_id": f"demo_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "name": "Vertigo Email Processing Demo",
        "input": "Processing demo email for Langwatch CTO meeting",
        "output": "Successfully processed email with Gemini LLM analysis",
        "metadata": {
            "system": "vertigo",
            "service": "email-processor",
            "model": "gemini-1.5-pro",
            "user_id": "vertigo_demo",
            "demo_meeting": "langwatch_cto",
            "timestamp": datetime.now().isoformat()
        },
        "type": "trace",
        "success": True
    }
    
    print("📊 Creating Langwatch trace...")
    print(f"   Trace ID: {trace_data['trace_id']}")
    print(f"   Project: {trace_data['project_id']}")
    
    try:
        # Try different API endpoints
        endpoints = [
            "https://app.langwatch.ai/api/traces",
            "https://api.langwatch.ai/traces", 
            "https://app.langwatch.ai/api/v1/traces"
        ]
        
        for endpoint in endpoints:
            print(f"🌐 Trying endpoint: {endpoint}")
            
            response = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Vertigo-Demo/1.0"
                },
                json=trace_data,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code in [200, 201]:
                print("✅ Successfully created Langwatch trace!")
                print(f"🎯 Check dashboard: https://app.langwatch.ai/eunoia-Eyh6Gz/analytics/users")
                return True
                
        print("❌ All endpoints failed")
        return False
        
    except Exception as e:
        print(f"❌ Error creating trace: {e}")
        return False

def create_multiple_demo_traces():
    """Create multiple traces for a better demo."""
    traces = [
        {
            "name": "Email Processing - Help Command",
            "input": "User requested help via email",
            "output": "Sent comprehensive help response with available commands"
        },
        {
            "name": "Meeting Transcript Analysis", 
            "input": "Analyzing meeting transcript with Gemini LLM",
            "output": "Generated semantic tags and summary for meeting"
        },
        {
            "name": "Daily Status Generation",
            "input": "Generating executive daily status from recent meetings", 
            "output": "Created executive summary and sent via Gmail"
        }
    ]
    
    success_count = 0
    for i, trace_info in enumerate(traces, 1):
        print(f"\n📝 Creating trace {i}/3: {trace_info['name']}")
        
        if create_langwatch_trace():
            success_count += 1
    
    print(f"\n🎉 Created {success_count}/3 demo traces!")
    print(f"🎯 View them at: https://app.langwatch.ai/eunoia-Eyh6Gz/analytics/users")

if __name__ == "__main__":
    print("🚀 Starting Langwatch Demo Trace Generation")
    print("=" * 50)
    
    create_multiple_demo_traces()
    
    print("\n🎤 Ready for your demo with the Langwatch CTO!")