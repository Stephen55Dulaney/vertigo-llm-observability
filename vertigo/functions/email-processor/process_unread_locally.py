#!/usr/bin/env python3
"""
Process unread emails locally to bypass the cloud function 500 error.
This script mimics what the email processor does but runs locally.
"""

import json
import base64
import requests
from email.mime.text import MIMEText
from google.cloud import secretmanager
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

MEETING_PROCESSOR_URL = "https://us-central1-vertigo-466116.cloudfunctions.net/meeting-processor-v2"

def get_secret(secret_name):
    """Retrieve a secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/vertigo-466116/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_gmail_service():
    """Get Gmail service with OAuth token from Secret Manager."""
    token_json = get_secret("gmail-oauth-token")
    creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    return service

def send_reply(service, original_msg, to_email, subject, body_text):
    """Send a reply email."""
    message = MIMEText(body_text)
    message['to'] = to_email
    message['from'] = "vertigo.agent.2025@gmail.com"
    message['subject'] = f"Re: {subject}"
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {
        'raw': raw,
        'threadId': original_msg.get('threadId') if original_msg else None
    }
    
    # Remove threadId if it's None to avoid the Invalid thread_id error
    if message_body['threadId'] is None:
        del message_body['threadId']
    
    sent = service.users().messages().send(userId='me', body=message_body).execute()
    logger.info(f"Sent email to {to_email}")
    return sent

def process_meeting_transcript(service, msg_data, sender_email, subject, body):
    """Process meeting transcript and send summary email."""
    logger.info(f"Processing meeting transcript: {subject}")
    
    try:
        # Call meeting processor
        payload = {
            "transcript": body,
            "transcript_type": "email",
            "project": "vertigo",
            "participants": [sender_email],
            "meeting_title": subject
        }
        
        response = requests.post(MEETING_PROCESSOR_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            resp_json = response.json()
            meeting_notes = resp_json.get('processed_notes', '')
            
            if meeting_notes and meeting_notes.strip():
                logger.info(f"Got meeting notes ({len(meeting_notes)} chars), sending reply...")
                
                # Send the meeting summary via email
                send_reply(service, msg_data, sender_email, subject, meeting_notes)
                logger.info(f"✅ Sent meeting summary to {sender_email}")
                return True
            else:
                logger.warning("No meeting notes content to send")
                return False
        else:
            logger.error(f"Meeting processor failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing meeting: {e}")
        return False

def is_vertigo_command(subject):
    """Check if email is a Vertigo command."""
    return subject and 'vertigo:' in subject.lower()

def is_status_request(subject, body):
    """Check if email is a status request."""
    text = (subject + " " + body).lower()
    return any(keyword in text for keyword in ['status request', 'generate status', 'status report'])

def is_daily_summary_request(subject, body):
    """Check if email is a daily summary request."""
    text = (subject + " " + body).lower()
    return any(keyword in text for keyword in ['3:00 pm', '3pm', 'daily summary', 'boss update'])

def process_unread_emails():
    """Process all unread emails and send meeting summaries."""
    logger.info("🔄 Processing unread emails locally...")
    
    try:
        service = get_gmail_service()
        
        # Get unread messages
        results = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()
        messages = results.get('messages', [])
        
        logger.info(f"Found {len(messages)} unread messages")
        
        processed_count = 0
        
        for msg in messages:
            try:
                msg_id = msg['id']
                msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                
                # Extract message details
                payload = msg_data['payload']
                headers = payload.get('headers', [])
                
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '(No Sender)')
                sender_email = sender.split('<')[-1].replace('>', '').strip() if '<' in sender else sender
                
                # Get message body
                body = ""
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            break
                elif payload.get('body', {}).get('data'):
                    body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                
                logger.info(f"📧 Email: '{subject}' from {sender_email}")
                
                # Route email based on classification
                if is_vertigo_command(subject):
                    logger.info("   → Vertigo command (skipping)")
                elif is_status_request(subject, body):
                    logger.info("   → Status request (skipping)")
                elif is_daily_summary_request(subject, body):
                    logger.info("   → Daily summary (skipping)")
                else:
                    logger.info("   → Processing as meeting transcript...")
                    if process_meeting_transcript(service, msg_data, sender_email, subject, body):
                        processed_count += 1
                        logger.info("   ✅ Meeting summary sent!")
                    else:
                        logger.info("   ❌ Failed to process meeting")
                
                # Mark as read
                service.users().messages().modify(
                    userId='me', 
                    id=msg_id, 
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                
            except Exception as e:
                logger.error(f"Error processing message {msg_id}: {e}")
                continue
        
        logger.info(f"✅ Processing complete!")
        logger.info(f"   Total unread: {len(messages)}")
        logger.info(f"   Meeting summaries sent: {processed_count}")
        
        return processed_count
        
    except Exception as e:
        logger.error(f"Error processing unread emails: {e}")
        return 0

if __name__ == "__main__":
    process_unread_emails()