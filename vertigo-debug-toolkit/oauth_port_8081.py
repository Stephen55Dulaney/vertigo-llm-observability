#!/usr/bin/env python3
"""
Gmail OAuth - Alternative Port 8081
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify', 
    'https://www.googleapis.com/auth/gmail.send'
]

CLIENT_SECRETS_FILE = "/Users/stephendulaney/Documents/KeyStorage/client_secret_579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com.json"

def main():
    print("🔑 GMAIL OAUTH (Port 8081)")
    print("📧 SELECT: vertigo.agent.2025@gmail.com")
    print("❌ NOT: stephen.dulaney@gmail.com")
    print()
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        
        # Use port 8081 instead of 8080
        creds = flow.run_local_server(
            port=8081,
            prompt='select_account',
            access_type='offline'
        )
        
        # Test credentials
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        
        email = profile.get('emailAddress')
        print(f"✅ Authorized: {email}")
        
        if email == "vertigo.agent.2025@gmail.com":
            # Save token
            with open('/Users/stephendulaney/Documents/Vertigo/token.json', 'w') as f:
                f.write(creds.to_json())
            print("🎉 SUCCESS! Token saved.")
            print("📧 Gmail automation restored!")
            return True
        else:
            print(f"❌ Wrong account: {email}")
            print("Need: vertigo.agent.2025@gmail.com")
            return False
            
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    main()