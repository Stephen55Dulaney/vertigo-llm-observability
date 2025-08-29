#!/usr/bin/env python3
"""
DEBUG SCRIPT 3: Test Full Email-to-Summary Pipeline
Tests the complete pipeline from email processing to summary delivery.

This script simulates the exact flow that should happen when an email is processed:
1. Calls email processor cloud function
2. Verifies meeting processor is called
3. Checks if send_reply() is triggered
4. Tests end-to-end email delivery
"""

import requests
import json
import logging
from datetime import datetime
from google.cloud import secretmanager
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cloud function endpoints
EMAIL_PROCESSOR_URL = "https://us-central1-vertigo-466116.cloudfunctions.net/email-processor-v2"
MEETING_PROCESSOR_URL = "https://us-central1-vertigo-466116.cloudfunctions.net/meeting-processor-v2"

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

def get_secret(secret_name):
    """Retrieve a secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/vertigo-466116/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_gmail_service():
    """Get Gmail service with OAuth token from Secret Manager."""
    try:
        token_json = get_secret("gmail-oauth-token")
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Error getting Gmail service: {e}")
        raise

def send_test_email_to_inbox():
    """Send a test meeting transcript email to trigger the pipeline."""
    logger.info("=" * 60)
    logger.info("SENDING TEST MEETING EMAIL TO TRIGGER PIPELINE")
    logger.info("=" * 60)
    
    try:
        service = get_gmail_service()
        
        # Create a test meeting transcript email
        test_subject = f"Vertigo Debug Meeting - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        test_body = f"""
Here is the transcript from our debugging session:

We are investigating why meeting summaries are not being automatically emailed to sdulaney@mergeworld.com. The system appears to process meetings correctly and store summaries in Firestore, but the email delivery is failing.

Key Discussion Points:
1. Meeting processor generates summaries successfully
2. Summaries are stored in Firestore database  
3. Email processor has send_reply() function for sending summaries
4. No summary emails found in Gmail sent items
5. Need to debug the complete pipeline flow

Technical Investigation:
- Verified meeting processor returns 'processed_notes' field
- Tested Gmail API send permissions independently
- Need to check if process_meeting_transcript() is called
- Need to verify email classification logic
- Need to trace the complete processing flow

Action Items:
1. Debug email classification - ensure meetings trigger correct handler
2. Add logging to track send_reply() calls
3. Test complete end-to-end pipeline
4. Check for any silent failures in the processing chain

Project: vertigo
Duration: 20 minutes
Participants: Stephen Dulaney, Thomas (Debugging Partner)

---
Test Email Generated: {datetime.now().isoformat()}
Purpose: Trigger automatic meeting summary processing and email delivery
        """.strip()
        
        # Send to self to trigger processing
        message = MIMEText(test_body)
        message['to'] = "me"  # Send to self
        message['from'] = "me"
        message['subject'] = test_subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message_body = {'raw': raw}
        
        sent = service.users().messages().send(userId='me', body=message_body).execute()
        
        logger.info(f"✅ TEST EMAIL SENT TO INBOX")
        logger.info(f"   Message ID: {sent.get('id')}")
        logger.info(f"   Subject: {test_subject}")
        logger.info(f"   This should trigger automatic processing when email-processor runs")
        
        return sent.get('id'), test_subject, test_body
        
    except Exception as e:
        logger.error(f"❌ FAILED TO SEND TEST EMAIL: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return None, None, None

def test_email_processor_direct():
    """Test email processor cloud function directly."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING EMAIL PROCESSOR CLOUD FUNCTION")
    logger.info("=" * 60)
    
    try:
        logger.info(f"Calling email processor: {EMAIL_PROCESSOR_URL}")
        
        # Call without payload to trigger normal unread email processing
        response = requests.post(EMAIL_PROCESSOR_URL, json={}, timeout=120)
        
        logger.info(f"HTTP Status Code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ EMAIL PROCESSOR FAILED")
            logger.error(f"Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
        # Parse response
        try:
            resp_json = response.json()
            logger.info(f"✅ EMAIL PROCESSOR SUCCESS")
            logger.info(f"Response: {json.dumps(resp_json, indent=2)}")
            
            processed_count = resp_json.get('processed_count', 0)
            total_messages = resp_json.get('total_messages', 0)
            
            logger.info(f"\n📧 EMAIL PROCESSING RESULTS:")
            logger.info(f"   Processed: {processed_count} emails")
            logger.info(f"   Total Unread: {total_messages} emails")
            
            if processed_count > 0:
                logger.info(f"✅ EMAILS WERE PROCESSED")
                logger.info(f"   Check Gmail sent items for summary replies")
            else:
                logger.warning(f"⚠️  NO EMAILS PROCESSED")
                logger.warning(f"   Either no unread emails or classification issue")
            
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ FAILED TO PARSE EMAIL PROCESSOR RESPONSE")
            logger.error(f"Error: {e}")
            logger.error(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"❌ EMAIL PROCESSOR TIMEOUT (120 seconds)")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ EMAIL PROCESSOR REQUEST FAILED: {e}")
        return False

def check_gmail_sent_items():
    """Check Gmail sent items for recent summary emails."""
    logger.info("\n" + "=" * 60)
    logger.info("CHECKING GMAIL SENT ITEMS FOR SUMMARY EMAILS")
    logger.info("=" * 60)
    
    try:
        service = get_gmail_service()
        
        # Get sent messages from the last 24 hours
        results = service.users().messages().list(
            userId='me', 
            labelIds=['SENT'],
            maxResults=20
        ).execute()
        
        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} recent sent messages")
        
        summary_emails = []
        
        for msg in messages[:10]:  # Check last 10 sent emails
            try:
                msg_id = msg['id']
                msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                payload = msg_data['payload']
                headers = payload.get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                to_addr = next((h['value'] for h in headers if h['name'] == 'To'), '(No To)')
                date_header = next((h['value'] for h in headers if h['name'] == 'Date'), '(No Date)')
                
                logger.info(f"\n📧 Sent Email:")
                logger.info(f"   Subject: {subject}")
                logger.info(f"   To: {to_addr}")
                logger.info(f"   Date: {date_header}")
                
                # Check if this looks like a meeting summary
                is_summary = (
                    'meeting' in subject.lower() or 
                    'summary' in subject.lower() or
                    'Re:' in subject or
                    'sdulaney@mergeworld.com' in to_addr
                )
                
                if is_summary:
                    summary_emails.append({
                        'subject': subject,
                        'to': to_addr,
                        'date': date_header,
                        'id': msg_id
                    })
                    logger.info(f"   ✅ POTENTIAL SUMMARY EMAIL FOUND")
                
            except Exception as e:
                logger.error(f"   Error checking message {msg_id}: {e}")
                continue
        
        logger.info(f"\n📊 SUMMARY EMAIL ANALYSIS:")
        logger.info(f"   Total Sent Messages Checked: {min(10, len(messages))}")
        logger.info(f"   Potential Summary Emails: {len(summary_emails)}")
        
        if summary_emails:
            logger.info(f"✅ FOUND RECENT SUMMARY EMAILS:")
            for email in summary_emails:
                logger.info(f"   • {email['subject']} → {email['to']}")
        else:
            logger.warning(f"⚠️  NO SUMMARY EMAILS FOUND IN RECENT SENT ITEMS")
            logger.warning(f"   This suggests send_reply() is not being called")
        
        return len(summary_emails) > 0
        
    except Exception as e:
        logger.error(f"❌ FAILED TO CHECK SENT ITEMS: {e}")
        return False

def main():
    """Run the complete pipeline debug test."""
    logger.info("Starting Full Email-to-Summary Pipeline Debug Test")
    logger.info("This will test the complete flow from email to summary delivery")
    
    # Step 1: Send test email to trigger pipeline
    msg_id, subject, body = send_test_email_to_inbox()
    
    if not msg_id:
        logger.error("❌ Cannot proceed - failed to send test email")
        return
    
    # Step 2: Wait a moment for email to arrive
    import time
    logger.info("\n⏳ Waiting 5 seconds for email to be delivered...")
    time.sleep(5)
    
    # Step 3: Check sent items BEFORE processing
    logger.info("\n🔍 CHECKING SENT ITEMS BEFORE PROCESSING:")
    sent_before = check_gmail_sent_items()
    
    # Step 4: Trigger email processor
    processor_success = test_email_processor_direct()
    
    # Step 5: Wait for processing to complete
    logger.info("\n⏳ Waiting 10 seconds for processing to complete...")
    time.sleep(10)
    
    # Step 6: Check sent items AFTER processing
    logger.info("\n🔍 CHECKING SENT ITEMS AFTER PROCESSING:")
    sent_after = check_gmail_sent_items()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("FULL PIPELINE TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Test Email Sent: {'✅ SUCCESS' if msg_id else '❌ FAILED'}")
    logger.info(f"Email Processor: {'✅ SUCCESS' if processor_success else '❌ FAILED'}")
    logger.info(f"Sent Items Before: {'✅ HAS SUMMARIES' if sent_before else '❌ NO SUMMARIES'}")
    logger.info(f"Sent Items After: {'✅ HAS SUMMARIES' if sent_after else '❌ NO SUMMARIES'}")
    
    if msg_id and processor_success and not sent_before and sent_after:
        logger.info("\n✅ SUCCESS: Pipeline working - new summary email was sent!")
    elif msg_id and processor_success and not sent_after:
        logger.error("\n❌ ISSUE: Email processed but no summary sent")
        logger.error("   Root cause: send_reply() not being called or failing silently")
    else:
        logger.error("\n❌ ISSUES DETECTED in pipeline")
        logger.error("   Need to investigate individual components")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()