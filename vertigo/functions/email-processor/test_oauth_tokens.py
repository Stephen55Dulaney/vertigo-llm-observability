#!/usr/bin/env python3
"""
Test OAuth Tokens Script
This script tests if the current OAuth tokens in Secret Manager are working.
"""

import json
from google.cloud import secretmanager
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Configuration
PROJECT_ID = "vertigo-466116"
SECRET_NAME = "gmail-oauth-token"
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

def get_secret(secret_name):
    """Retrieve a secret from Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"❌ Error retrieving secret {secret_name}: {e}")
        return None

def test_gmail_connection():
    """Test Gmail API connection using tokens from Secret Manager."""
    print("🧪 Testing Gmail OAuth tokens from Secret Manager...")
    print(f"Project: {PROJECT_ID}")
    print(f"Secret: {SECRET_NAME}")
    print()
    
    # Get OAuth token from Secret Manager
    print("📥 Retrieving token from Secret Manager...")
    token_json = get_secret(SECRET_NAME)
    
    if not token_json:
        return False
    
    try:
        token_data = json.loads(token_json)
        print("✅ Successfully retrieved token from Secret Manager")
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing token JSON: {e}")
        return False
    
    # Check token structure
    required_fields = ['token', 'refresh_token', 'token_uri', 'client_id', 'client_secret']
    missing_fields = [field for field in required_fields if field not in token_data]
    
    if missing_fields:
        print(f"❌ Token missing required fields: {missing_fields}")
        return False
    
    print("✅ Token structure is valid")
    
    # Create credentials
    try:
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        print("✅ Successfully created credentials from token")
    except Exception as e:
        print(f"❌ Error creating credentials: {e}")
        return False
    
    # Test Gmail API connection
    try:
        print("🔗 Testing Gmail API connection...")
        service = build('gmail', 'v1', credentials=creds)
        
        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress')
        messages_total = profile.get('messagesTotal', 0)
        
        print(f"✅ Successfully connected to Gmail API")
        print(f"✅ Authenticated as: {email_address}")
        print(f"✅ Total messages in account: {messages_total}")
        
        # Test retrieving messages
        results = service.users().messages().list(userId='me', maxResults=1).execute()
        messages = results.get('messages', [])
        
        if messages:
            print(f"✅ Successfully retrieved messages (found {len(messages)} in sample)")
        else:
            print("⚠️ No messages found in account")
        
        print("\n🎉 OAuth tokens are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Gmail API test failed: {e}")
        print("This likely means the OAuth tokens have expired or are invalid.")
        return False

def main():
    """Main function to test OAuth tokens."""
    print("🔍 GMAIL OAUTH TOKEN VERIFICATION")
    print("=" * 40)
    print()
    
    success = test_gmail_connection()
    
    if success:
        print("\n✅ Token verification completed successfully!")
        print("The cloud function should be able to access Gmail.")
    else:
        print("\n❌ Token verification failed!")
        print("You need to refresh the OAuth tokens using refresh_oauth_tokens.py")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)