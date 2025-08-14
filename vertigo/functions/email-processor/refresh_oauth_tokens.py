#!/usr/bin/env python3
"""
Complete OAuth Token Refresh Script for Gmail API
This script handles the complete process of refreshing OAuth tokens and updating Secret Manager.
"""

import os
import json
import subprocess
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.cloud import secretmanager

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

# Project configuration
PROJECT_ID = "vertigo-466116"
SECRET_NAME = "gmail-oauth-token"
CLIENT_SECRETS_FILE = "client_secret_579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com.json"
TOKEN_FILE = "token.json"
GMAIL_ACCOUNT = "vertigo.agent.2025@gmail.com"

def print_setup_instructions():
    """Print comprehensive setup instructions."""
    print("🔧 GMAIL OAUTH TOKEN REFRESH PROCESS")
    print("=" * 50)
    print()
    print("This script will:")
    print("1. Generate fresh OAuth tokens for Gmail API access")
    print("2. Save tokens locally to token.json")
    print("3. Upload tokens to Google Cloud Secret Manager")
    print()
    print("Prerequisites:")
    print("- Google Cloud CLI installed and authenticated")
    print("- OAuth client credentials file present")
    print("- Access to the Gmail account: vertigo.agent.2025@gmail.com")
    print()
    
def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check if client secrets file exists
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"❌ Error: OAuth client credentials file not found!")
        print(f"Expected: {CLIENT_SECRETS_FILE}")
        print("Please download from Google Cloud Console and place in this directory.")
        return False
    else:
        print(f"✅ OAuth client credentials file found")
    
    # Check Google Cloud CLI
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Google Cloud CLI installed")
        else:
            print("❌ Google Cloud CLI not working properly")
            return False
    except FileNotFoundError:
        print("❌ Google Cloud CLI not installed")
        print("Please install: https://cloud.google.com/sdk/docs/install")
        return False
    
    # Check if authenticated with Google Cloud
    try:
        result = subprocess.run(['gcloud', 'auth', 'list', '--filter=status:ACTIVE'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("✅ Google Cloud CLI authenticated")
        else:
            print("❌ Google Cloud CLI not authenticated")
            print("Please run: gcloud auth login")
            return False
    except Exception as e:
        print(f"❌ Error checking Google Cloud auth: {e}")
        return False
    
    print("✅ All prerequisites met")
    return True

def generate_fresh_tokens():
    """Generate fresh OAuth tokens using the authorization flow."""
    print("\n🔑 Generating fresh OAuth tokens...")
    
    creds = None
    
    # Load existing token if available (for refresh)
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Warning: Could not load existing token: {e}")
    
    # If no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Attempting to refresh expired token...")
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                print("Will start fresh authorization flow...")
                creds = None
        
        if not creds:
            print(f"\n🌐 Starting OAuth authorization flow...")
            print(f"Please sign in with: {GMAIL_ACCOUNT}")
            print("A browser window will open...")
            
            # Create the flow using the client secrets file
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            # Use port 8081 which should be authorized
            creds = flow.run_local_server(port=8081, prompt='consent')
            print("✅ OAuth authorization completed")
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"✅ Token saved to {TOKEN_FILE}")
    else:
        print("✅ Valid token already exists")
    
    return creds

def prepare_secret_data(creds):
    """Prepare token data for Secret Manager."""
    print("\n📋 Preparing token data for Secret Manager...")
    
    # Convert to dictionary for Secret Manager
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    
    print("✅ Token data prepared")
    return token_data

def update_secret_manager(token_data):
    """Update the OAuth token in Google Cloud Secret Manager."""
    print(f"\n☁️ Updating Secret Manager secret: {SECRET_NAME}...")
    
    try:
        # Save token data to temporary file
        temp_file = "temp_token.json"
        with open(temp_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        # Use gcloud command to update secret
        cmd = [
            'gcloud', 'secrets', 'versions', 'add', SECRET_NAME,
            '--data-file', temp_file,
            '--project', PROJECT_ID
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temp file
        os.remove(temp_file)
        
        if result.returncode == 0:
            print(f"✅ Secret {SECRET_NAME} updated successfully in project {PROJECT_ID}")
            print("The cloud function can now access Gmail with the fresh tokens")
            return True
        else:
            print(f"❌ Error updating secret: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating Secret Manager: {e}")
        return False

def verify_tokens():
    """Verify that the tokens work by testing Gmail API access."""
    print("\n🧪 Verifying tokens work with Gmail API...")
    
    try:
        from googleapiclient.discovery import build
        
        # Load tokens
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        
        # Test API call - get user profile
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress')
        
        print(f"✅ Successfully connected to Gmail API")
        print(f"✅ Authenticated as: {email_address}")
        
        if email_address == GMAIL_ACCOUNT:
            print("✅ Correct Gmail account authenticated")
            return True
        else:
            print(f"⚠️ Warning: Expected {GMAIL_ACCOUNT}, got {email_address}")
            return False
            
    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        return False

def main():
    """Main function to orchestrate the token refresh process."""
    print_setup_instructions()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please resolve issues above and try again.")
        return False
    
    print("\n🚀 Starting OAuth token refresh process...")
    
    # Generate fresh tokens
    try:
        creds = generate_fresh_tokens()
    except Exception as e:
        print(f"❌ Failed to generate tokens: {e}")
        return False
    
    # Prepare secret data
    token_data = prepare_secret_data(creds)
    
    # Verify tokens work
    if verify_tokens():
        # Update Secret Manager
        if update_secret_manager(token_data):
            print("\n🎉 OAuth token refresh completed successfully!")
            print("\nNext steps:")
            print("1. Test the cloud function to ensure it can access Gmail")
            print("2. Monitor logs for any authentication errors")
            print(f"3. The secret '{SECRET_NAME}' is now updated in project '{PROJECT_ID}'")
            return True
        else:
            print("\n❌ Failed to update Secret Manager")
            return False
    else:
        print("\n❌ Token verification failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)