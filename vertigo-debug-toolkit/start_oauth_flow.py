#!/usr/bin/env python3
"""
Gmail OAuth Re-authorization Flow
Guides through the complete OAuth process with clear instructions.
"""

import os
import json
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes - exactly what Vertigo needs
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify', 
    'https://www.googleapis.com/auth/gmail.send'
]

CLIENT_SECRETS_FILE = "/Users/stephendulaney/Documents/KeyStorage/client_secret_579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com.json"

def print_instructions():
    """Print clear step-by-step instructions."""
    print("🔑 GMAIL OAUTH RE-AUTHORIZATION")
    print("=" * 50)
    print()
    print("📧 CRITICAL: You MUST select the correct email account!")
    print()
    print("✅ CORRECT EMAIL: vertigo.agent.2025@gmail.com")
    print("❌ WRONG EMAIL:   stephen.dulaney@gmail.com (your personal account)")
    print("❌ WRONG EMAIL:   Any other Gmail account")
    print()
    print("🔄 WHAT WILL HAPPEN:")
    print("1. Browser will open to Google OAuth page")
    print("2. You'll see a list of Gmail accounts")
    print("3. ⚠️  SELECT: vertigo.agent.2025@gmail.com")
    print("4. Grant permissions for Gmail access")
    print("5. Authorization will complete automatically")
    print()
    print("🚨 IF YOU SEE MULTIPLE ACCOUNTS:")
    print("   - Look for: vertigo.agent.2025@gmail.com")
    print("   - DO NOT select stephen.dulaney@gmail.com")
    print("   - If vertigo account not visible, click 'Use another account'")
    print()

def start_oauth_flow():
    """Start the OAuth authorization flow."""
    
    print_instructions()
    
    # Confirm user is ready
    input("Press ENTER when you're ready to start the OAuth flow...")
    print()
    
    try:
        print("🚀 Starting OAuth flow...")
        print("📂 Using client secrets file:", CLIENT_SECRETS_FILE)
        
        # Check if client secrets file exists
        if not os.path.exists(CLIENT_SECRETS_FILE):
            print(f"❌ ERROR: Client secrets file not found!")
            print(f"Expected location: {CLIENT_SECRETS_FILE}")
            return False
        
        print("✅ Client secrets file found")
        print()
        print("🌐 Opening browser for authorization...")
        print("👀 REMEMBER: Select vertigo.agent.2025@gmail.com")
        print()
        
        # Create the OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, 
            SCOPES
        )
        
        # Run the flow - this will open the browser
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',  # Force consent screen to show accounts
            access_type='offline'  # Get refresh token
        )
        
        print()
        print("🎉 AUTHORIZATION SUCCESSFUL!")
        print()
        
        # Save the credentials
        token_file = "/Users/stephendulaney/Documents/Vertigo/token.json"
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        
        print(f"✅ Token saved to: {token_file}")
        
        # Test the credentials
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        
        email_address = profile.get('emailAddress')
        print(f"📧 Authorized email: {email_address}")
        
        if email_address == "vertigo.agent.2025@gmail.com":
            print("✅ CORRECT! You selected the right account!")
            print("🔥 Gmail automation is now restored!")
        else:
            print("❌ WARNING: You selected the wrong account!")
            print(f"   Selected: {email_address}")
            print(f"   Expected: vertigo.agent.2025@gmail.com")
            print("   Please run this script again and select the correct account.")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth flow failed: {e}")
        print()
        print("💡 TROUBLESHOOTING:")
        print("1. Make sure you selected vertigo.agent.2025@gmail.com")
        print("2. Try running the script again")
        print("3. Check if localhost:8080 is available")
        return False

if __name__ == "__main__":
    success = start_oauth_flow()
    if success:
        print()
        print("🎯 NEXT STEPS:")
        print("1. Test email processing with new token")
        print("2. Update Google Cloud Secret Manager")
        print("3. Verify automated email processing works")
    else:
        print()
        print("🔄 Please try again and make sure to:")
        print("   📧 Select: vertigo.agent.2025@gmail.com")
        print("   ❌ NOT:    stephen.dulaney@gmail.com")