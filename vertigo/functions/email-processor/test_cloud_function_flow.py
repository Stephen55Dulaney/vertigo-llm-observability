#!/usr/bin/env python3
"""
Test Cloud Function OAuth Flow
This script simulates exactly how the cloud function retrieves and uses OAuth tokens.
"""

import json
import subprocess
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Configuration - exactly as in main.py
PROJECT_ID = "vertigo-466116"
SECRET_NAME = "gmail-oauth-token"
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

def get_secret_via_gcloud(secret_name):
    """Retrieve a secret from Secret Manager using gcloud command (bypasses ADC issues)."""
    try:
        cmd = ['gcloud', 'secrets', 'versions', 'access', 'latest', 
               '--secret', secret_name, '--project', PROJECT_ID]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"❌ Error retrieving secret: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Error running gcloud command: {e}")
        return None

def get_gmail_service_like_cloud_function():
    """Get Gmail service exactly like the cloud function does."""
    try:
        print("📥 Retrieving OAuth token from Secret Manager (like cloud function)...")
        
        # Get OAuth token from Secret Manager using gcloud
        token_json = get_secret_via_gcloud(SECRET_NAME)
        if not token_json:
            return None
            
        print("✅ Successfully retrieved token from Secret Manager")
        
        # Parse and create credentials (exactly like cloud function)
        token_data = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        print("✅ Successfully created credentials from Secret Manager token")
        
        # Build Gmail service (exactly like cloud function)
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Successfully built Gmail service")
        
        return service
        
    except Exception as e:
        print(f"❌ Error getting Gmail service: {e}")
        return None

def test_cloud_function_simulation():
    """Simulate the cloud function's email processing flow."""
    print("🧪 Testing cloud function OAuth flow simulation...")
    print(f"Project: {PROJECT_ID}")
    print(f"Secret: {SECRET_NAME}")
    print()
    
    # Get Gmail service like the cloud function
    service = get_gmail_service_like_cloud_function()
    if not service:
        return False
    
    try:
        print("\n🔗 Testing Gmail API operations (like cloud function)...")
        
        # Test 1: Get user profile
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress')
        print(f"✅ Profile: {email_address}")
        
        # Test 2: List unread messages (exactly like cloud function)
        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD']).execute()
        messages = results.get('messages', [])
        print(f"✅ Found {len(messages)} unread messages")
        
        # Test 3: Get a message if available (like cloud function)
        if messages:
            msg_id = messages[0]['id']
            msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = msg_data['payload']
            headers = payload.get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '(No Sender)')
            print(f"✅ Sample message: '{subject}' from {sender}")
        
        print("\n🎉 Cloud function OAuth simulation successful!")
        print("The cloud function should now be able to process emails correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Cloud function simulation failed: {e}")
        return False

def main():
    """Main function to test cloud function OAuth flow."""
    print("☁️ CLOUD FUNCTION OAUTH FLOW SIMULATION")
    print("=" * 50)
    print()
    
    success = test_cloud_function_simulation()
    
    if success:
        print("\n✅ Cloud function simulation completed successfully!")
        print("\nNext steps:")
        print("1. The OAuth tokens are fresh and working")
        print("2. Secret Manager has been updated with the new tokens")
        print("3. The cloud function should now be able to access Gmail")
        print("4. Test the actual cloud function to confirm it's working")
    else:
        print("\n❌ Cloud function simulation failed!")
        print("Please check the OAuth tokens and Secret Manager configuration.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)