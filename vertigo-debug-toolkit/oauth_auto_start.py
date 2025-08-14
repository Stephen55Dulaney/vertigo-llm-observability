#!/usr/bin/env python3
"""
Gmail OAuth Re-authorization - Auto Start Version
Immediately starts the OAuth flow without waiting for input.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify', 
    'https://www.googleapis.com/auth/gmail.send'
]

CLIENT_SECRETS_FILE = "/Users/stephendulaney/Documents/KeyStorage/client_secret_579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com.json"

def main():
    print("🔑 GMAIL OAUTH RE-AUTHORIZATION")
    print("=" * 50)
    print()
    print("📧 CRITICAL INSTRUCTION:")
    print("   ✅ SELECT: vertigo.agent.2025@gmail.com")
    print("   ❌ NOT:    stephen.dulaney@gmail.com")
    print()
    print("🌐 Browser will open in 3 seconds...")
    print("🎯 Remember to select the VERTIGO email account!")
    print()
    
    try:
        # Check if client secrets file exists
        if not os.path.exists(CLIENT_SECRETS_FILE):
            print(f"❌ ERROR: Client secrets file not found!")
            print(f"Expected: {CLIENT_SECRETS_FILE}")
            return False
        
        print("🚀 Starting OAuth flow...")
        
        # Create and run the OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, 
            SCOPES
        )
        
        # This will open the browser and wait for authorization
        creds = flow.run_local_server(
            port=8080,
            prompt='select_account',  # Show account selection
            access_type='offline'     # Get refresh token
        )
        
        print()
        print("🎉 AUTHORIZATION COMPLETED!")
        
        # Test the credentials to verify correct account
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        
        email_address = profile.get('emailAddress')
        print(f"📧 Authorized account: {email_address}")
        
        if email_address == "vertigo.agent.2025@gmail.com":
            print("✅ SUCCESS! Correct Vertigo account selected!")
            
            # Save token locally
            token_file = "/Users/stephendulaney/Documents/Vertigo/token.json"
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"💾 Token saved to: {token_file}")
            
            # Show next steps
            print()
            print("🎯 WHAT'S RESTORED:")
            print("   ✅ Gmail API access")
            print("   ✅ Automatic email processing")
            print("   ✅ Meeting transcript processing")
            print("   ✅ Status report generation")
            
            return True
        else:
            print("❌ WRONG ACCOUNT SELECTED!")
            print(f"   You selected: {email_address}")
            print(f"   Need to select: vertigo.agent.2025@gmail.com")
            print()
            print("🔄 Please run this script again and:")
            print("   1. Look for vertigo.agent.2025@gmail.com in the account list")
            print("   2. Click 'Use another account' if needed")
            print("   3. Do NOT select your personal Gmail")
            
            return False
        
    except Exception as e:
        print(f"❌ OAuth flow failed: {e}")
        print()
        print("💡 Common issues:")
        print("   - Browser blocked the popup")
        print("   - Selected wrong account") 
        print("   - Port 8080 already in use")
        print("   - Network connectivity issue")
        
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print()
        print("🚀 READY TO UPDATE CLOUD SECRETS!")
        print("Run this next:")
        print("   python update_cloud_token.py")
    else:
        print()
        print("🔄 Try again: python oauth_auto_start.py")