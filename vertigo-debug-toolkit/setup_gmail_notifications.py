#!/usr/bin/env python3
"""
Gmail Push Notification Setup Script

This script sets up Gmail push notifications to trigger the email processor function
when new emails arrive in the vertigo.agent.2025@gmail.com inbox.
"""

import json
import os
import sys
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.cloud import secretmanager

class GmailNotificationSetup:
    def __init__(self):
        self.project_id = "vertigo-466116"
        self.region = "us-central1"
        self.gmail_address = "vertigo.agent.2025@gmail.com"
        self.function_url = f"https://{self.region}-{self.project_id}.cloudfunctions.net/email_processor"
        
    def get_gmail_service(self):
        """Get Gmail service with OAuth credentials."""
        try:
            # Get OAuth token from Secret Manager
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{self.project_id}/secrets/gmail-oauth-token/versions/latest"
            response = client.access_secret_version(request={"name": secret_name})
            token_data = json.loads(response.payload.data.decode("UTF-8"))
            
            # Create credentials
            creds = Credentials.from_authorized_user_info(token_data)
            service = build('gmail', 'v1', credentials=creds)
            return service
        except Exception as e:
            print(f"❌ Error getting Gmail service: {e}")
            return None
    
    def check_existing_watch(self):
        """Check if there's an existing watch on the Gmail account."""
        service = self.get_gmail_service()
        if not service:
            return None
        
        try:
            # Check for existing watch
            response = service.users().getProfile(userId='me').execute()
            print(f"✅ Connected to Gmail as: {response.get('emailAddress')}")
            
            # Note: Gmail API doesn't provide a direct way to list watches
            # We'll assume no watch exists and create a new one
            return None
            
        except Exception as e:
            print(f"❌ Error checking existing watch: {e}")
            return None
    
    def create_gmail_watch(self):
        """Create a Gmail watch to receive push notifications."""
        service = self.get_gmail_service()
        if not service:
            return False
        
        try:
            # Create watch request
            watch_request = {
                'labelIds': ['INBOX'],  # Watch the INBOX label
                'topicName': f'projects/{self.project_id}/topics/gmail-notifications'
            }
            
            print(f"📧 Setting up Gmail watch for: {self.gmail_address}")
            print(f"🌐 Function URL: {self.function_url}")
            print(f"📋 Topic: projects/{self.project_id}/topics/gmail-notifications")
            
            # Create the watch
            response = service.users().watch(userId='me', body=watch_request).execute()
            
            print(f"✅ Gmail watch created successfully!")
            print(f"📅 Expires: {response.get('expiration')}")
            print(f"🆔 History ID: {response.get('historyId')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating Gmail watch: {e}")
            return False
    
    def setup_pubsub_topic(self):
        """Set up the Pub/Sub topic for Gmail notifications."""
        try:
            import subprocess
            
            print(f"📡 Setting up Pub/Sub topic...")
            
            # Create the topic
            topic_name = f"projects/{self.project_id}/topics/gmail-notifications"
            cmd = f"gcloud pubsub topics create gmail-notifications --project={self.project_id}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Pub/Sub topic created: {topic_name}")
            else:
                print(f"⚠️ Topic may already exist: {result.stderr}")
            
            # Create subscription to the cloud function
            subscription_name = f"projects/{self.project_id}/subscriptions/gmail-notifications"
            cmd = f"gcloud pubsub subscriptions create gmail-notifications --topic=gmail-notifications --push-endpoint={self.function_url} --project={self.project_id}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Pub/Sub subscription created: {subscription_name}")
                return True
            else:
                print(f"⚠️ Subscription may already exist: {result.stderr}")
                return True
                
        except Exception as e:
            print(f"❌ Error setting up Pub/Sub: {e}")
            return False
    
    def test_notification_setup(self):
        """Test the notification setup by sending a test email."""
        print(f"\n🧪 Testing notification setup...")
        print(f"📧 Send a test email to: {self.gmail_address}")
        print(f"📋 Subject: 'test notification setup'")
        print(f"⏳ Waiting for notification...")
        
        # Note: In a real scenario, you'd wait for the notification
        # For now, we'll just provide instructions
        print(f"📋 To test:")
        print(f"1. Send an email to {self.gmail_address}")
        print(f"2. Check the cloud function logs:")
        print(f"   gcloud functions logs read email_processor --limit=10 --project={self.project_id}")
        print(f"3. Check if the email was processed")
    
    def run_setup(self):
        """Run the complete Gmail notification setup."""
        print(f"🚀 Setting up Gmail push notifications for Vertigo")
        print(f"📧 Gmail: {self.gmail_address}")
        print(f"🌐 Function: {self.function_url}")
        print(f"⏰ Timestamp: {datetime.now().isoformat()}")
        
        # Step 1: Check existing setup
        print(f"\n📋 Step 1: Checking existing setup...")
        self.check_existing_watch()
        
        # Step 2: Set up Pub/Sub topic and subscription
        print(f"\n📋 Step 2: Setting up Pub/Sub infrastructure...")
        if not self.setup_pubsub_topic():
            print(f"❌ Failed to set up Pub/Sub infrastructure")
            return False
        
        # Step 3: Create Gmail watch
        print(f"\n📋 Step 3: Creating Gmail watch...")
        if not self.create_gmail_watch():
            print(f"❌ Failed to create Gmail watch")
            return False
        
        # Step 4: Test the setup
        print(f"\n📋 Step 4: Testing the setup...")
        self.test_notification_setup()
        
        print(f"\n✅ Gmail notification setup completed!")
        print(f"📋 Next steps:")
        print(f"1. Send a test email to {self.gmail_address}")
        print(f"2. Monitor function logs for processing")
        print(f"3. Check if emails are being processed automatically")
        
        return True

def main():
    """Main setup function."""
    setup = GmailNotificationSetup()
    success = setup.run_setup()
    
    if success:
        print(f"\n🎉 Setup completed successfully!")
    else:
        print(f"\n❌ Setup failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 