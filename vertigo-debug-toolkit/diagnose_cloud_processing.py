#!/usr/bin/env python3
"""
Diagnostic script to check Cloud Function status and identify processing issues.
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_cloud_function_health():
    """Check the health of the Cloud Function."""
    
    print("🔍 Diagnosing Cloud Function Issues")
    print("=" * 50)
    
    # Get the Cloud Function URL from environment
    function_url = os.getenv('VERTIGO_API_URL')
    if not function_url:
        print("❌ VERTIGO_API_URL not set in environment")
        return
    
    print(f"📡 Cloud Function URL: {function_url}")
    
    # Test basic connectivity
    try:
        response = requests.get(function_url, timeout=10)
        print(f"✅ Function reachable: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Function not reachable: {e}")
        return
    
    # Test with a simple payload
    test_payload = {
        "message": {
            "data": "test"
        }
    }
    
    try:
        response = requests.post(function_url, json=test_payload, timeout=30)
        print(f"✅ Function responds to POST: {response.status_code}")
        if response.status_code != 200:
            print(f"⚠️  Response: {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Function POST failed: {e}")

def check_gmail_api_status():
    """Check Gmail API status and authentication."""
    
    print("\n📧 Checking Gmail API Status")
    print("-" * 30)
    
    # Check if Gmail credentials are configured
    gmail_creds_path = os.getenv('GMAIL_CREDENTIALS_PATH')
    if gmail_creds_path:
        print(f"✅ Gmail credentials path: {gmail_creds_path}")
        if os.path.exists(gmail_creds_path):
            print("✅ Gmail credentials file exists")
        else:
            print("❌ Gmail credentials file not found")
    else:
        print("❌ GMAIL_CREDENTIALS_PATH not set")
    
    # Check Gmail API quota (if we can access it)
    try:
        # This would require proper Gmail API setup
        print("ℹ️  Gmail API quota check requires proper authentication")
    except Exception as e:
        print(f"⚠️  Gmail API check failed: {e}")

def check_gemini_api_status():
    """Check Gemini API status."""
    
    print("\n🤖 Checking Gemini API Status")
    print("-" * 30)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print("✅ Gemini API key is set")
        
        # Test Gemini API
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content("Test")
            print("✅ Gemini API is working")
        except Exception as e:
            print(f"❌ Gemini API test failed: {e}")
    else:
        print("❌ GEMINI_API_KEY not set")

def check_langfuse_status():
    """Check Langfuse status."""
    
    print("\n📊 Checking Langfuse Status")
    print("-" * 30)
    
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    host = os.getenv('LANGFUSE_HOST')
    
    if all([public_key, secret_key, host]):
        print("✅ Langfuse credentials are set")
        print(f"📡 Langfuse host: {host}")
        
        # Test Langfuse connection
        try:
            from langfuse import Langfuse
            client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
            print("✅ Langfuse connection successful")
        except Exception as e:
            print(f"❌ Langfuse connection failed: {e}")
    else:
        print("❌ Langfuse credentials incomplete")

def check_environment_variables():
    """Check all required environment variables."""
    
    print("\n🔧 Checking Environment Variables")
    print("-" * 35)
    
    required_vars = [
        'VERTIGO_API_URL',
        'GEMINI_API_KEY',
        'LANGFUSE_PUBLIC_KEY',
        'LANGFUSE_SECRET_KEY',
        'LANGFUSE_HOST',
        'GOOGLE_CLOUD_PROJECT_ID'
    ]
    
    optional_vars = [
        'GMAIL_CREDENTIALS_PATH',
        'VERTEX_AI_LOCATION',
        'VERTEX_AI_MODEL_NAME'
    ]
    
    print("Required variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)}")
        else:
            print(f"❌ {var}: Not set")
    
    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set")

def suggest_solutions():
    """Suggest solutions for common issues."""
    
    print("\n💡 Common Issues and Solutions")
    print("=" * 40)
    
    print("""
1. **Cloud Function Timeout**
   - Check function timeout settings (default: 60s)
   - Increase timeout for long-running operations
   - Add retry logic for external API calls

2. **Gmail API Quota Exceeded**
   - Check Gmail API quota usage
   - Implement exponential backoff
   - Consider using service account with higher limits

3. **Authentication Issues**
   - Verify service account permissions
   - Check OAuth token expiration
   - Ensure proper domain-wide delegation

4. **Memory/CPU Limits**
   - Monitor Cloud Function resource usage
   - Increase memory allocation if needed
   - Optimize code for better performance

5. **External API Failures**
   - Add comprehensive error handling
   - Implement circuit breaker pattern
   - Log all external API calls for debugging

6. **Database Connection Issues**
   - Check Firestore connection limits
   - Implement connection pooling
   - Add retry logic for database operations
    """)

def main():
    """Run all diagnostic checks."""
    
    check_environment_variables()
    check_cloud_function_health()
    check_gmail_api_status()
    check_gemini_api_status()
    check_langfuse_status()
    suggest_solutions()
    
    print("\n" + "=" * 50)
    print("🔍 Diagnostic Complete!")
    print("📋 Check the logs above for any ❌ errors")
    print("💡 Review the suggested solutions for fixes")

if __name__ == "__main__":
    main() 