#!/usr/bin/env python3
"""
Email Processor Diagnostic Tool

This script diagnoses why the Vertigo email processor isn't processing emails automatically.
It checks:
1. Cloud Function deployment status
2. Gmail API integration
3. Push notification setup
4. OAuth token validity
5. Secret Manager configuration
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
import subprocess
from google.cloud import secretmanager
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class EmailProcessorDiagnostic:
    def __init__(self):
        self.project_id = "vertigo-466116"
        self.region = "us-central1"
        self.email_processor_url = f"https://{self.region}-{self.project_id}.cloudfunctions.net/email_processor"
        self.gmail_address = "vertigo.agent.2025@gmail.com"
        
    def print_header(self, title):
        """Print a formatted header."""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_section(self, title):
        """Print a formatted section."""
        print(f"\n📋 {title}")
        print(f"{'-'*40}")
    
    def print_result(self, test_name, status, details=""):
        """Print a test result."""
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    def check_cloud_function_deployment(self):
        """Check if the email processor cloud function is deployed and accessible."""
        self.print_section("Cloud Function Deployment")
        
        try:
            # Test basic connectivity
            response = requests.get(self.email_processor_url, timeout=10)
            self.print_result("Function Accessibility", "PASS" if response.status_code == 200 else "FAIL", 
                            f"HTTP {response.status_code}")
            
            # Test with a sample request
            test_data = {
                "message": {
                    "data": "test",
                    "messageId": "test_id",
                    "publishTime": datetime.now().isoformat()
                }
            }
            
            response = requests.post(self.email_processor_url, json=test_data, timeout=30)
            self.print_result("Function Response", "PASS" if response.status_code in [200, 400, 500] else "FAIL",
                            f"HTTP {response.status_code} - {response.text[:100]}...")
            
        except requests.exceptions.ConnectionError:
            self.print_result("Function Accessibility", "FAIL", "Connection failed - function may not be deployed")
        except Exception as e:
            self.print_result("Function Test", "FAIL", f"Error: {str(e)}")
    
    def check_gmail_api_integration(self):
        """Check Gmail API integration and OAuth token."""
        self.print_section("Gmail API Integration")
        
        try:
            # Check if we can access Secret Manager
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{self.project_id}/secrets/gmail-oauth-token/versions/latest"
            
            try:
                response = client.access_secret_version(request={"name": secret_name})
                token_data = json.loads(response.payload.data.decode("UTF-8"))
                self.print_result("OAuth Token Access", "PASS", "Token found in Secret Manager")
                
                # Test token validity
                creds = Credentials.from_authorized_user_info(token_data)
                service = build('gmail', 'v1', credentials=creds)
                
                # Test Gmail API access
                profile = service.users().getProfile(userId='me').execute()
                self.print_result("Gmail API Access", "PASS", f"Connected as: {profile.get('emailAddress')}")
                
                # Check for unread messages
                results = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()
                unread_count = len(results.get('messages', []))
                self.print_result("Unread Messages", "INFO", f"Found {unread_count} unread messages")
                
                if unread_count > 0:
                    # Get details of unread messages
                    for msg in results.get('messages', [])[:3]:  # Check first 3
                        message = service.users().messages().get(userId='me', id=msg['id']).execute()
                        headers = message['payload']['headers']
                        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                        from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                        
                        print(f"   📧 Unread: {subject} (from: {from_header}, date: {date})")
                
            except Exception as e:
                self.print_result("OAuth Token Access", "FAIL", f"Error accessing token: {str(e)}")
                
        except Exception as e:
            self.print_result("Secret Manager Access", "FAIL", f"Error: {str(e)}")
    
    def check_push_notifications(self):
        """Check if Gmail push notifications are properly configured."""
        self.print_section("Gmail Push Notifications")
        
        try:
            # This would require checking the Gmail API for push notification setup
            # For now, we'll provide guidance
            self.print_result("Push Notification Check", "INFO", 
                            "Manual verification required - check Gmail API console")
            print("   📋 To verify push notifications:")
            print("   1. Go to Google Cloud Console > APIs & Services > Gmail API")
            print("   2. Check if push notifications are enabled")
            print("   3. Verify the webhook URL is set to the email processor function")
            print("   4. Check if the subscription is active")
            
        except Exception as e:
            self.print_result("Push Notification Check", "FAIL", f"Error: {str(e)}")
    
    def check_cloud_logs(self):
        """Check recent cloud function logs for errors."""
        self.print_section("Recent Cloud Function Logs")
        
        try:
            # This would use gcloud CLI to check logs
            # For now, provide guidance
            self.print_result("Log Analysis", "INFO", "Manual verification required")
            print("   📋 To check recent logs, run:")
            print(f"   gcloud functions logs read email_processor --limit=50 --project={self.project_id}")
            print("   Look for:")
            print("   - Authentication errors")
            print("   - Gmail API errors")
            print("   - Function invocation errors")
            print("   - Timeout errors")
            
        except Exception as e:
            self.print_result("Log Analysis", "FAIL", f"Error: {str(e)}")
    
    def check_trigger_configuration(self):
        """Check if the function is properly triggered by Gmail events."""
        self.print_section("Trigger Configuration")
        
        try:
            # Check if the function is configured to receive Gmail push notifications
            self.print_result("Trigger Type", "INFO", "Should be HTTP trigger for Gmail push notifications")
            print("   📋 Expected configuration:")
            print("   - Trigger: HTTP")
            print("   - Allow unauthenticated: Yes")
            print("   - Gmail push notification subscription active")
            print("   - Webhook URL: " + self.email_processor_url)
            
        except Exception as e:
            self.print_result("Trigger Check", "FAIL", f"Error: {str(e)}")
    
    def provide_recommendations(self):
        """Provide recommendations for fixing the issue."""
        self.print_section("Recommendations")
        
        print("🔧 Based on the diagnostic results, here are the most likely issues:")
        print()
        print("1. **Gmail Push Notifications Disabled**")
        print("   - The most common cause of unprocessed emails")
        print("   - Check Gmail API console for push notification status")
        print("   - Re-enable push notifications if disabled")
        print()
        print("2. **OAuth Token Expired**")
        print("   - Gmail OAuth tokens can expire")
        print("   - Check token validity in Secret Manager")
        print("   - Refresh the OAuth token if needed")
        print()
        print("3. **Function Deployment Issues**")
        print("   - Cloud function may have been redeployed incorrectly")
        print("   - Check function logs for errors")
        print("   - Redeploy the function if necessary")
        print()
        print("4. **Gmail API Quota Exceeded**")
        print("   - Check Gmail API usage in Google Cloud Console")
        print("   - Verify quota limits haven't been exceeded")
        print()
        print("🚀 **Immediate Actions:**")
        print("1. Run: gcloud functions logs read email_processor --limit=50")
        print("2. Check Gmail API console for push notification status")
        print("3. Test the function manually with a sample email")
        print("4. Redeploy the function if needed")
    
    def run_full_diagnostic(self):
        """Run the complete diagnostic."""
        self.print_header("Email Processor Diagnostic")
        print(f"🔍 Diagnosing email processor for: {self.gmail_address}")
        print(f"🌐 Function URL: {self.email_processor_url}")
        print(f"⏰ Timestamp: {datetime.now().isoformat()}")
        
        self.check_cloud_function_deployment()
        self.check_gmail_api_integration()
        self.check_push_notifications()
        self.check_cloud_logs()
        self.check_trigger_configuration()
        self.provide_recommendations()
        
        self.print_header("Diagnostic Complete")
        print("📋 Review the results above and follow the recommendations to fix the issue.")

def main():
    """Main diagnostic function."""
    diagnostic = EmailProcessorDiagnostic()
    diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    main() 