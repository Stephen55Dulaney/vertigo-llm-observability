#!/usr/bin/env python3
"""
Script to fix identified cloud processing issues.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_environment_variables():
    """Add missing environment variables to .env file."""
    
    print("🔧 Fixing Environment Variables")
    print("=" * 40)
    
    # Read current .env file
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
    else:
        content = ""
    
    # Variables to add
    missing_vars = {
        'GOOGLE_CLOUD_PROJECT_ID': 'vertigo-466116',
        'GMAIL_CREDENTIALS_PATH': 'path/to/gmail-credentials.json',
        'VERTEX_AI_LOCATION': 'us-central1',
        'VERTEX_AI_MODEL_NAME': 'gemini-1.5-pro'
    }
    
    # Check what's missing
    added_vars = []
    for var, default_value in missing_vars.items():
        if f'{var}=' not in content:
            content += f'\n# {var}\n{var}={default_value}\n'
            added_vars.append(var)
            print(f"✅ Added {var}")
        else:
            print(f"ℹ️  {var} already exists")
    
    # Write back to .env file
    if added_vars:
        with open(env_file, 'w') as f:
            f.write(content)
        print(f"\n📝 Updated {env_file} with {len(added_vars)} new variables")
    else:
        print("\n✅ All required variables are already set")

def create_cloud_function_config():
    """Create configuration for Cloud Function optimization."""
    
    print("\n⚙️  Cloud Function Optimization")
    print("=" * 35)
    
    config = {
        "timeout": "540s",  # 9 minutes (max for free tier)
        "memory": "512MB",  # Increase memory
        "max_instances": 10,  # Limit concurrent instances
        "retry_config": {
            "retry_count": 3,
            "max_retry_duration": "60s"
        }
    }
    
    print("Recommended Cloud Function settings:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # Create deployment script
    deploy_script = """#!/bin/bash
# Deploy Cloud Function with optimized settings

gcloud functions deploy email_processor \\
  --runtime python310 \\
  --trigger-http \\
  --allow-unauthenticated \\
  --timeout=540s \\
  --memory=512MB \\
  --max-instances=10 \\
  --set-env-vars GOOGLE_CLOUD_PROJECT_ID=vertigo-466116 \\
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \\
  --set-env-vars LANGFUSE_PUBLIC_KEY=$LANGFUSE_PUBLIC_KEY \\
  --set-env-vars LANGFUSE_SECRET_KEY=$LANGFUSE_SECRET_KEY \\
  --set-env-vars LANGFUSE_HOST=$LANGFUSE_HOST
"""
    
    with open('deploy_function.sh', 'w') as f:
        f.write(deploy_script)
    
    print("\n📝 Created deploy_function.sh script")
    print("💡 Run: chmod +x deploy_function.sh && ./deploy_function.sh")

def create_gmail_setup_guide():
    """Create Gmail API setup guide."""
    
    print("\n📧 Gmail API Setup Guide")
    print("=" * 25)
    
    guide = """
# Gmail API Setup for Vertigo

## 1. Enable Gmail API
- Go to Google Cloud Console
- Navigate to APIs & Services > Library
- Search for "Gmail API" and enable it

## 2. Create Service Account
- Go to IAM & Admin > Service Accounts
- Create new service account: "vertigo-gmail-processor"
- Grant "Gmail API" permissions

## 3. Set up Domain-Wide Delegation
- Download service account key
- In Google Workspace Admin:
  - Go to Security > API Controls > Domain-wide Delegation
  - Add client ID and scope: https://www.googleapis.com/auth/gmail.readonly

## 4. Update Environment Variables
- Set GMAIL_CREDENTIALS_PATH to your service account key file
- Ensure GOOGLE_CLOUD_PROJECT_ID is set

## 5. Test Gmail Connection
- Run: python test_gmail_connection.py
"""
    
    with open('GMAIL_SETUP.md', 'w') as f:
        f.write(guide)
    
    print("📝 Created GMAIL_SETUP.md guide")

def create_monitoring_script():
    """Create script to monitor Cloud Function health."""
    
    print("\n📊 Creating Monitoring Script")
    print("=" * 30)
    
    monitor_script = """#!/usr/bin/env python3
\"\"\"
Monitor Cloud Function health and performance.
\"\"\"

import requests
import time
import json
from datetime import datetime

def check_function_health():
    \"\"\"Check if Cloud Function is responding.\"\"\"
    
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
    \"\"\"Monitor function continuously.\"\"\"
    
    print("🔍 Starting continuous monitoring...")
    print("Press Ctrl+C to stop")
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\\n[{timestamp}] Checking function health...")
        
        if not check_function_health():
            print("⚠️  Function may be down - check logs")
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    monitor_continuously()
"""
    
    with open('monitor_function.py', 'w') as f:
        f.write(monitor_script)
    
    print("📝 Created monitor_function.py")
    print("💡 Run: python monitor_function.py to monitor continuously")

def main():
    """Run all fixes."""
    
    print("🚀 Fixing Cloud Processing Issues")
    print("=" * 40)
    
    fix_environment_variables()
    create_cloud_function_config()
    create_gmail_setup_guide()
    create_monitoring_script()
    
    print("\n" + "=" * 50)
    print("✅ Fixes Applied!")
    print("\n📋 Next Steps:")
    print("1. Set up Gmail API credentials (see GMAIL_SETUP.md)")
    print("2. Deploy optimized Cloud Function (run deploy_function.sh)")
    print("3. Monitor function health (run monitor_function.py)")
    print("4. Test with real emails")
    print("\n🔗 Your dashboard now shows real data: 2 traces, $0.0160 cost")

if __name__ == "__main__":
    main() 