#!/usr/bin/env python3
"""
Gmail Token Refresh Script
Uses the refresh token to get a new access token.
"""

import json
import requests
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_current_token_from_secret_manager():
    """Get current token from Google Cloud Secret Manager."""
    try:
        result = subprocess.run([
            'gcloud', 'secrets', 'versions', 'access', 'latest', 
            '--secret=gmail-oauth-token'
        ], capture_output=True, text=True, check=True)
        
        return json.loads(result.stdout)
    except Exception as e:
        logger.error(f"Failed to get token from Secret Manager: {e}")
        return None

def refresh_access_token(token_data):
    """Refresh the access token using the refresh token."""
    try:
        refresh_url = "https://oauth2.googleapis.com/token"
        
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': token_data['refresh_token'],
            'client_id': token_data['client_id'],
            'client_secret': token_data['client_secret']
        }
        
        logger.info("🔄 Refreshing Gmail OAuth token...")
        response = requests.post(refresh_url, data=payload, timeout=30)
        response.raise_for_status()
        
        new_token_data = response.json()
        logger.info("✅ Successfully refreshed OAuth token!")
        
        # Update the token data with new access token
        token_data['token'] = new_token_data['access_token']
        
        # Some refresh responses include a new refresh token
        if 'refresh_token' in new_token_data:
            token_data['refresh_token'] = new_token_data['refresh_token']
            logger.info("📝 Received new refresh token")
        
        return token_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to refresh token: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        return None

def update_secret_manager(token_data):
    """Update the token in Google Cloud Secret Manager."""
    try:
        # Write token to temporary file
        temp_file = "/tmp/gmail_token.json"
        with open(temp_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        # Update secret in Secret Manager
        result = subprocess.run([
            'gcloud', 'secrets', 'versions', 'add', 'gmail-oauth-token',
            '--data-file', temp_file
        ], capture_output=True, text=True, check=True)
        
        logger.info("✅ Updated token in Google Cloud Secret Manager")
        
        # Clean up temp file
        import os
        os.remove(temp_file)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to update Secret Manager: {e}")
        return False

def test_token(token_data):
    """Test the refreshed token by making a Gmail API call."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        # Create credentials from token data
        creds = Credentials.from_authorized_user_info(token_data)
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        
        # Test with a simple API call
        profile = service.users().getProfile(userId='me').execute()
        
        logger.info(f"✅ Token test successful! Connected to: {profile.get('emailAddress')}")
        logger.info(f"📊 Total messages: {profile.get('messagesTotal', 0)}")
        
        # Check for unread messages
        unread_query = service.users().messages().list(
            userId='me', 
            labelIds=['INBOX', 'UNREAD'],
            maxResults=10
        ).execute()
        
        unread_count = len(unread_query.get('messages', []))
        logger.info(f"📧 Unread messages: {unread_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Token test failed: {e}")
        return False

def main():
    """Main refresh process."""
    print("🔑 GMAIL OAUTH TOKEN REFRESH")
    print("=" * 40)
    print()
    
    # Step 1: Get current token from Secret Manager
    logger.info("1️⃣ Getting current token from Secret Manager...")
    token_data = get_current_token_from_secret_manager()
    if not token_data:
        logger.error("❌ Failed to get current token")
        return False
    
    logger.info(f"   📧 Account: {token_data.get('client_id', 'Unknown')}")
    logger.info(f"   🔑 Has refresh token: {'Yes' if token_data.get('refresh_token') else 'No'}")
    
    # Step 2: Refresh the access token
    logger.info("2️⃣ Refreshing access token...")
    new_token_data = refresh_access_token(token_data)
    if not new_token_data:
        logger.error("❌ Failed to refresh token")
        return False
    
    # Step 3: Update Secret Manager
    logger.info("3️⃣ Updating Secret Manager...")
    if not update_secret_manager(new_token_data):
        logger.error("❌ Failed to update Secret Manager")
        return False
    
    # Step 4: Test the new token
    logger.info("4️⃣ Testing refreshed token...")
    if not test_token(new_token_data):
        logger.error("❌ Token test failed")
        return False
    
    print()
    print("🎉 GMAIL OAUTH TOKEN REFRESH COMPLETE!")
    print("✅ Your email processing should now work automatically")
    print("✅ The Cloud Functions can now access Gmail")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)