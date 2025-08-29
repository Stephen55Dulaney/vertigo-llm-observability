#!/usr/bin/env python3
"""
OAuth with updated Gmail API scopes
"""

import json
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

# Updated Gmail API scopes - using current format
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

CLIENT_SECRETS_FILE = "client_secret_579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com.json"

def create_oauth_flow():
    """Create OAuth flow with updated scopes."""
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = 'http://localhost:8080/oauth2callback'
    return flow

def get_authorization_url():
    """Get authorization URL with updated scopes."""
    flow = create_oauth_flow()
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )
    return flow, auth_url

def complete_oauth_flow(auth_code):
    """Complete OAuth flow with authorization code."""
    try:
        # Create the flow
        flow = create_oauth_flow()
        
        # Exchange authorization code for credentials
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        
        # Save token
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'universe_domain': 'googleapis.com',
            'account': '',
            'expiry': creds.expiry.isoformat() if creds.expiry else None
        }
        
        with open('token.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print("✅ Token saved to token.json")
        
        # Test the credentials
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress')
        
        print(f"✅ Successfully connected to Gmail API")
        print(f"✅ Authenticated as: {email_address}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error completing OAuth: {e}")
        return False

def main():
    if len(sys.argv) == 2:
        # Authorization code provided
        auth_code = sys.argv[1]
        success = complete_oauth_flow(auth_code)
        sys.exit(0 if success else 1)
    else:
        # Generate authorization URL with updated scopes
        flow, auth_url = get_authorization_url()
        
        print("🔗 OAuth Authorization with Updated Scopes")
        print("=" * 50)
        print()
        print("1. Copy and open this URL in your browser:")
        print()
        print(auth_url)
        print()
        print("2. Sign in with: vertigo.agent.2025@gmail.com")
        print("3. Grant permissions")
        print("4. Copy the authorization code from redirect URL")
        print("5. Run: python3 updated_oauth.py YOUR_CODE")
        print()

if __name__ == "__main__":
    main()