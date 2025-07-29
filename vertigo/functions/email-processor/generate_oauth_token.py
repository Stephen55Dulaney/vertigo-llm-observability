#!/usr/bin/env python3
"""
Script to generate OAuth token for Gmail API access.
Run this once to get the token, then store it in Secret Manager.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

def generate_oauth_token():
    """Generate OAuth token for Gmail API access."""
    
    # Path to your OAuth client credentials file
    # Update this path to where you downloaded the client_secret_*.json file
    CLIENT_SECRETS_FILE = "client_secret_579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com.json"
    
    # Check if token file already exists
    TOKEN_FILE = "token.json"
    
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Create the flow using the client secrets file
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    # Convert to dictionary for Secret Manager
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    
    print("OAuth token generated successfully!")
    print("Token data (store this in Secret Manager):")
    print(json.dumps(token_data, indent=2))
    
    return token_data

if __name__ == "__main__":
    # Copy your OAuth client credentials file to this directory first
    if not os.path.exists("client_secret_579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com.json"):
        print("Error: OAuth client credentials file not found!")
        print("Please download the client_secret_*.json file from Google Cloud Console")
        print("and place it in this directory.")
        exit(1)
    
    generate_oauth_token() 