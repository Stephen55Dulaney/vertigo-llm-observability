#!/usr/bin/env python3
"""
Test Local OAuth Tokens Script
This script tests the locally generated OAuth tokens to verify they work with Gmail API.
"""

import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Configuration
TOKEN_FILE = "token.json"
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

def test_local_gmail_connection():
    """Test Gmail API connection using local token.json file."""
    print("🧪 Testing local OAuth tokens...")
    print(f"Token file: {TOKEN_FILE}")
    print()
    
    # Load token from local file
    try:
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
        print("✅ Successfully loaded local token file")
    except FileNotFoundError:
        print(f"❌ Token file {TOKEN_FILE} not found")
        return False
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
        
        # Test retrieving unread messages
        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=5).execute()
        unread_messages = results.get('messages', [])
        
        print(f"✅ Found {len(unread_messages)} unread messages")
        
        if unread_messages:
            print("✅ Sample unread message IDs:")
            for i, msg in enumerate(unread_messages[:3]):
                print(f"   {i+1}. {msg['id']}")
        
        print("\n🎉 Local OAuth tokens are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Gmail API test failed: {e}")
        return False

def main():
    """Main function to test local OAuth tokens."""
    print("🔍 LOCAL GMAIL OAUTH TOKEN VERIFICATION")
    print("=" * 45)
    print()
    
    success = test_local_gmail_connection()
    
    if success:
        print("\n✅ Local token verification completed successfully!")
        print("The OAuth tokens are working and should also work in the cloud function.")
    else:
        print("\n❌ Local token verification failed!")
        print("Please run refresh_oauth_tokens.py to generate new tokens.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)