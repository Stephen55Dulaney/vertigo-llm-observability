#!/usr/bin/env python3
"""
Manual OAuth Token Setup Instructions

Since the automated OAuth flow is having issues, here's how to manually create the token:
"""

import json
import os

def print_manual_setup_instructions():
    """Print manual setup instructions for OAuth token."""
    
    print("🔧 MANUAL OAUTH TOKEN SETUP")
    print("=" * 50)
    print()
    print("Since the automated OAuth flow is having issues, follow these steps:")
    print()
    print("1. Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/apis/credentials")
    print()
    print("2. Find the OAuth 2.0 Client ID:")
    print("   579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com")
    print()
    print("3. Click on it to edit the configuration")
    print()
    print("4. Add these Authorized redirect URIs:")
    print("   - http://localhost:8080")
    print("   - http://localhost:8081")
    print("   - http://localhost:8082")
    print()
    print("5. Save the changes")
    print()
    print("6. Then run the OAuth script again:")
    print("   python generate_oauth_token.py")
    print()
    print("7. When the browser opens, sign in with: vertigo.agent.2025@gmail.com")
    print()
    print("8. After successful authentication, the token will be saved to token.json")
    print()
    print("9. Upload the token to Secret Manager:")
    print("   gcloud secrets versions add gmail-oauth-token --data-file=token.json --project=vertigo-466116")
    print()

def create_sample_token_structure():
    """Create a sample token structure for reference."""
    
    sample_token = {
        "token": "YOUR_ACCESS_TOKEN_HERE",
        "refresh_token": "YOUR_REFRESH_TOKEN_HERE", 
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com",
        "client_secret": "YOUR_CLIENT_SECRET_HERE",
        "scopes": [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify", 
            "https://www.googleapis.com/auth/gmail.send"
        ]
    }
    
    print("📋 SAMPLE TOKEN STRUCTURE:")
    print("=" * 30)
    print(json.dumps(sample_token, indent=2))
    print()

if __name__ == "__main__":
    print_manual_setup_instructions()
    create_sample_token_structure() 