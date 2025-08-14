#!/usr/bin/env python3
"""
OAuth Token Maintenance Guide
This script provides instructions and commands for maintaining Gmail OAuth tokens.
"""

import os
import json
from datetime import datetime, timezone

def check_token_expiry():
    """Check when the current local token expires."""
    try:
        with open('token.json', 'r') as f:
            token_data = json.load(f)
        
        if 'expiry' in token_data:
            expiry_str = token_data['expiry']
            # Parse the expiry datetime
            expiry_dt = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            if expiry_dt > now:
                time_left = expiry_dt - now
                hours_left = time_left.total_seconds() / 3600
                print(f"✅ Token expires: {expiry_dt} ({hours_left:.1f} hours from now)")
                return True
            else:
                print(f"❌ Token expired: {expiry_dt}")
                return False
        else:
            print("⚠️ No expiry information in token")
            return None
    except FileNotFoundError:
        print("❌ No local token.json file found")
        return False
    except Exception as e:
        print(f"❌ Error checking token expiry: {e}")
        return False

def print_maintenance_guide():
    """Print comprehensive OAuth maintenance guide."""
    print("🔧 GMAIL OAUTH TOKEN MAINTENANCE GUIDE")
    print("=" * 50)
    print()
    
    print("📋 Available Scripts:")
    print("=" * 20)
    print("1. refresh_oauth_tokens.py     - Complete OAuth token refresh process")
    print("2. test_local_tokens.py        - Test local OAuth tokens")
    print("3. test_cloud_function_flow.py - Simulate cloud function OAuth flow")
    print("4. oauth_maintenance_guide.py  - This guide")
    print()
    
    print("🔄 Regular Maintenance Process:")
    print("=" * 35)
    print("Gmail OAuth tokens expire approximately every hour.")
    print("When they expire, the cloud function will fail to access Gmail.")
    print()
    print("Signs of expired tokens:")
    print("- Cloud function logs show authentication errors")
    print("- Emails are not being processed")
    print("- 'invalid_grant' or 'invalid_token' errors")
    print()
    
    print("To refresh tokens:")
    print("1. cd vertigo/functions/email-processor")
    print("2. python3 refresh_oauth_tokens.py")
    print("3. Follow the browser authentication flow")
    print("4. Script will automatically update Secret Manager")
    print()
    
    print("🧪 Testing Process:")
    print("=" * 20)
    print("After refreshing tokens, verify they work:")
    print("1. python3 test_local_tokens.py          # Test local tokens")
    print("2. python3 test_cloud_function_flow.py   # Test Secret Manager tokens")
    print()
    
    print("☁️ Secret Manager Information:")
    print("=" * 32)
    print(f"Project ID: vertigo-466116")
    print(f"Secret Name: gmail-oauth-token")
    print(f"Gmail Account: vertigo.agent.2025@gmail.com")
    print()
    print("Manual Secret Manager commands:")
    print("# View secret versions:")
    print("gcloud secrets versions list gmail-oauth-token --project=vertigo-466116")
    print()
    print("# View current secret (first 50 chars of token):")
    print("gcloud secrets versions access latest --secret=gmail-oauth-token --project=vertigo-466116 | jq -r '.token' | head -c 50")
    print()
    
    print("🚨 Troubleshooting:")
    print("=" * 20)
    print("If refresh fails:")
    print("1. Check OAuth client credentials file exists:")
    print("   client_secret_579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com.json")
    print()
    print("2. Verify Google Cloud CLI is authenticated:")
    print("   gcloud auth list")
    print("   gcloud auth login (if needed)")
    print()
    print("3. Check project is set correctly:")
    print("   gcloud config get-value project")
    print("   gcloud config set project vertigo-466116 (if needed)")
    print()
    print("4. If browser doesn't open, copy the URL manually")
    print("5. Ensure you sign in with: vertigo.agent.2025@gmail.com")
    print()
    
    print("📅 Recommended Schedule:")
    print("=" * 25)
    print("- Check token status daily (automated monitoring recommended)")
    print("- Refresh tokens immediately when cloud function fails")
    print("- Consider setting up automatic token refresh (future enhancement)")
    print()

def main():
    """Main function to display maintenance guide."""
    print_maintenance_guide()
    
    print("🔍 Current Token Status:")
    print("=" * 25)
    check_token_expiry()
    print()
    
    print("🎯 Quick Commands:")
    print("=" * 17)
    print("# Refresh tokens now:")
    print("python3 refresh_oauth_tokens.py")
    print()
    print("# Test current tokens:")
    print("python3 test_local_tokens.py")
    print()
    print("# Check Secret Manager:")
    print("gcloud secrets versions list gmail-oauth-token --project=vertigo-466116")

if __name__ == "__main__":
    main()