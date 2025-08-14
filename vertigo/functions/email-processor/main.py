import functions_framework
from google.cloud import secretmanager
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import base64
import requests
import email
from email.mime.text import MIMEText
import json
import os
import tempfile
import logging
from datetime import datetime
from langfuse_client import langfuse_client
from langwatch_client import langwatch_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email-processor")

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

PROJECTS = ['vertigo', 'memento', 'gemino']

# Meeting processor endpoint
meeting_processor_url = "https://us-central1-vertigo-466116.cloudfunctions.net/meeting-processor-v2"
status_generator_url = "https://us-central1-vertigo-466116.cloudfunctions.net/status-generator"

# Email command patterns
VERTIGO_COMMANDS = [
    'list this week',
    'total stats', 
    'list projects',
    'help',
    'prompt report'
]

def is_vertigo_command(subject):
    """Check if email subject contains a Vertigo command."""
    subject_lower = subject.lower().strip()
    
    # Remove common reply/forward prefixes
    if subject_lower.startswith('re:'):
        subject_lower = subject_lower[3:].strip()
    elif subject_lower.startswith('fwd:'):
        subject_lower = subject_lower[4:].strip()
    
    # Check for Vertigo prefix
    if subject_lower.startswith('vertigo:'):
        subject_lower = subject_lower[8:].strip()
    
    return any(subject_lower.startswith(cmd) for cmd in VERTIGO_COMMANDS)

def process_vertigo_command(subject, body, sender):
    """Process Vertigo email commands and return response."""
    try:
        # Import the command parser (you'll need to add this file to the function)
        from email_command_parser import EmailCommandParser
        
        parser = EmailCommandParser()
        result = parser.parse_command(subject, body)
        
        if result:
            return {
                'success': True,
                'subject': result['subject'],
                'body': result['body'],
                'command': result['command']
            }
        else:
            return {
                'success': False,
                'error': 'No matching command found'
            }
            
    except Exception as e:
        logger.error(f"Error processing Vertigo command: {e}")
        return {
            'success': False,
            'error': f'Error processing command: {str(e)}'
        }

def get_secret(secret_name):
    """Retrieve a secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/vertigo-466116/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_gmail_service():
    """Get Gmail service with OAuth token from Secret Manager."""
    try:
        # Get OAuth token from Secret Manager
        token_json = get_secret("gmail-oauth-token")
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Error getting Gmail service: {e}")
        raise

def get_email_body(payload):
    """Extract email body from Gmail message payload."""
    if 'data' in payload['body']:
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    else:
        # If multipart, get the first part
        parts = payload.get('parts', [])
        for part in parts:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    return ''

def detect_project(subject, body):
    """Detect project from email subject and body."""
    text = (subject + " " + body).lower()
    for project in PROJECTS:
        if project in text:
            return project
    return "unknown"

def is_status_request(subject, body):
    """Check if this is a status request email."""
    status_keywords = ['status', 'generate status', 'status report', 'summary']
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    return any(keyword in subject_lower or keyword in body_lower for keyword in status_keywords)

def is_daily_summary_request(subject, body):
    """Check if this is a 3:00 PM daily summary request."""
    daily_summary_keywords = ['3:00', '3:00 pm', '3pm', 'daily summary', 'boss update', 'daily update']
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    return any(keyword in subject_lower or keyword in body_lower for keyword in daily_summary_keywords)

def send_reply(service, original_msg, to_email, subject, body_text):
    """Send a reply email."""
    message = MIMEText(body_text)
    message['to'] = to_email
    message['from'] = "me"
    message['subject'] = f"Re: {subject}"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {
        'raw': raw,
        'threadId': original_msg.get('threadId')
    }
    sent = service.users().messages().send(userId='me', body=message_body).execute()
    logger.info(f"Sent auto-reply to {to_email}")

def process_meeting_transcript(service, msg_data, subject, body, sender):
    """Process a meeting transcript email."""
    project = detect_project(subject, body)
    logger.info(f"Processing meeting transcript for project: {project}")
    
    # Send to meeting processor
    payload_json = {
        "transcript": body,
        "transcript_type": "dictation",
        "project": project,
        "participants": [],
        "duration_minutes": 45,
        "meeting_title": subject
    }
    
    try:
        response = requests.post(meeting_processor_url, json=payload_json)
        logger.info(f"Meeting processor HTTP status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Meeting processor returned status {response.status_code}: {response.text}")
            raise Exception(f"Meeting processor failed with status {response.status_code}")
        
        resp_json = response.json()
        logger.info(f"Meeting processor response: {resp_json}")
        
        # Auto-reply with meeting notes
        meeting_notes = resp_json.get('processed_notes', '')
        sender_email = email.utils.parseaddr(sender)[1]
        
        # Only send reply if we have content
        if meeting_notes and meeting_notes.strip():
            send_reply(service, msg_data, sender_email, subject, meeting_notes)
        else:
            logger.warning("No meeting notes content to send in auto-reply")
        
        return resp_json
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to meeting processor failed: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse meeting processor response as JSON: {e}")
        logger.error(f"Response text: {response.text}")
        raise
    except Exception as e:
        logger.error(f"Error in process_meeting_transcript: {e}")
        raise

def process_status_request(service, msg_data, subject, body, sender):
    """Process a status request email."""
    logger.info("Processing status request")
    
    # Extract status request from email body
    request_text = body.strip()
    if not request_text:
        request_text = "generate status"  # Default request
    
    # Send to status generator
    payload_json = {
        "request_text": request_text,
        "recipient_email": email.utils.parseaddr(sender)[1]
    }
    
    try:
        response = requests.post(status_generator_url, json=payload_json)
        logger.info(f"Status generator HTTP status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Status generator returned status {response.status_code}: {response.text}")
            raise Exception(f"Status generator failed with status {response.status_code}")
        
        resp_json = response.json()
        logger.info(f"Status generator response: {resp_json}")
        
        # Auto-reply with status update
        status_update = resp_json.get('status_update', '')
        sender_email = email.utils.parseaddr(sender)[1]
        
        # Only send reply if we have content
        if status_update and status_update.strip():
            send_reply(service, msg_data, sender_email, subject, status_update)
        else:
            logger.warning("No status update content to send in auto-reply")
        
        return resp_json
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to status generator failed: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse status generator response as JSON: {e}")
        logger.error(f"Response text: {response.text}")
        raise
    except Exception as e:
        logger.error(f"Error in process_status_request: {e}")
        raise

def process_daily_summary(service, msg_data, subject, body, sender):
    """Process a 3:00 PM daily summary request."""
    logger.info("Processing daily summary request")
    
    # Extract the daily content from email body
    daily_content = body.strip()
    if not daily_content:
        daily_content = "No daily content provided"  # Default content
    
    # Detect project from subject or body
    project = detect_project(subject, body)
    
    # Send to meeting processor with daily_summary prompt variant
    payload_json = {
        "transcript": daily_content,
        "transcript_type": "daily_summary",
        "project": project,
        "participants": [],
        "duration_minutes": 0,
        "meeting_title": subject,
        "prompt_variant": "daily_summary"  # Use the new daily summary prompt
    }
    
    try:
        response = requests.post(meeting_processor_url, json=payload_json)
        logger.info(f"Meeting processor HTTP status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Meeting processor returned status {response.status_code}: {response.text}")
            raise Exception(f"Meeting processor failed with status {response.status_code}")
        
        resp_json = response.json()
        logger.info(f"Daily summary processor response: {resp_json}")
        
        # Auto-reply with daily summary
        daily_summary = resp_json.get('processed_notes', '')
        sender_email = email.utils.parseaddr(sender)[1]
        
        # Only send reply if we have content
        if daily_summary and daily_summary.strip():
            # Create a professional subject for the reply
            reply_subject = f"Daily Summary - {project.title()} - {datetime.now().strftime('%Y-%m-%d')}"
            send_reply(service, msg_data, sender_email, reply_subject, daily_summary)
        else:
            logger.warning("No daily summary content to send in auto-reply")
        
        return resp_json
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to meeting processor failed: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse meeting processor response as JSON: {e}")
        logger.error(f"Response text: {response.text}")
        raise
    except Exception as e:
        logger.error(f"Error in process_daily_summary: {e}")
        raise

def generate_automatic_daily_summary(recipient_email="sdulaney@mergeworld.com"):
    """Generate and send an automatic 5:30 PM end-of-day summary."""
    logger.info(f"Generating automatic end-of-day summary for {recipient_email}")
    
    try:
        service = get_gmail_service()
        
        # Create a sample daily summary content based on typical work activities
        # This would ideally pull from a database or other source of daily activities
        daily_content = """
End-of-Day Work Summary:

My Ambition:
Complete the LLM observability tools evaluation framework and establish a working head-to-head comparison system for Langfuse, PromptLayer, and LangSmith to inform strategic decisions for WhoKnows and Gemino.

What We Did Today:
Successfully extended LangSmith evaluator with A/B testing and LLM-as-a-Judge capabilities, supporting Gemini and Claude models alongside OpenAI. Resolved multiple integration issues across all three evaluation environments, ensuring LangSmith (port 5028) is fully operational with comprehensive tracing, dataset evaluations, and advanced prompt testing features.

What We'll Do Next:
Test the new A/B testing and LLM-as-a-Judge features in LangSmith to validate their effectiveness for prompt optimization. Complete the evaluation framework by ensuring all three tools (LangSmith, PromptLayer, Langfuse) are fully operational and generating comparable data. Begin systematic testing of prompts across all platforms to gather performance metrics for the final evaluation report to AI Garage.
        """.strip()
        
        # Detect project (default to vertigo for now)
        project = "vertigo"
        
        # Send to meeting processor with daily_summary prompt variant
        payload_json = {
            "transcript": daily_content,
            "transcript_type": "daily_summary",
            "project": project,
            "participants": [],
            "duration_minutes": 0,
            "meeting_title": "End-of-Day Summary - 5:30 PM",
            "prompt_variant": "daily_summary"
        }
        
        response = requests.post(meeting_processor_url, json=payload_json)
        logger.info(f"Meeting processor HTTP status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Meeting processor returned status {response.status_code}: {response.text}")
            raise Exception(f"Meeting processor failed with status {response.status_code}")
        
        resp_json = response.json()
        logger.info(f"Daily summary processor response: {resp_json}")
        
        # Get the processed summary
        daily_summary = resp_json.get('processed_notes', '')
        
        if not daily_summary or not daily_summary.strip():
            # Fallback to a basic summary if processing failed
            daily_summary = f"""
End-of-Day Summary - {datetime.now().strftime('%Y-%m-%d')}

{daily_content}

---
Generated automatically by Vertigo Agent
            """.strip()
        
        # Send the summary email
        subject = f"End-of-Day Summary - {project.title()} - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Create email message
        message = MIMEText(daily_summary)
        message['to'] = recipient_email
        message['from'] = "me"
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message_body = {'raw': raw}
        
        # Send the email
        sent = service.users().messages().send(userId='me', body=message_body).execute()
        logger.info(f"Sent automatic end-of-day summary to {recipient_email}")
        
        return {
            'status': 'success',
            'message': f'End-of-day summary sent to {recipient_email}',
            'message_id': sent.get('id')
        }
        
    except Exception as e:
        logger.error(f"Error generating automatic end-of-day summary: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

def process_unread_emails(request=None):
    """Process all unread emails in the inbox."""
    # Create main trace for email processing
    trace_id = langfuse_client.create_trace(
        name="email_processing_batch",
        metadata={
            "operation": "process_unread_emails",
            "service": "email-processor",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    try:
        service = get_gmail_service()
        
        # Get unread messages
        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD']).execute()
        messages = results.get('messages', [])
        logger.info(f'Found {len(messages)} unread messages.')
        
        processed_count = 0
        
        for msg in messages:
            try:
                msg_id = msg['id']
                msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                payload = msg_data['payload']
                headers = payload.get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '(No Sender)')
                
                logger.info(f"Processing email: {subject} from {sender}")
                
                # Create span for individual email processing
                email_span_id = langfuse_client.create_span(
                    trace_id=trace_id,
                    name="process_individual_email",
                    metadata={
                        "email_id": msg_id,
                        "subject": subject,
                        "sender": sender
                    }
                )
                
                body = get_email_body(payload)
                
                # Determine if this is a status request or meeting transcript
                if is_vertigo_command(subject):
                    logger.info(f"Processing Vertigo command: {subject}")
                    command_result = process_vertigo_command(subject, body, sender)
                    
                    if command_result['success']:
                        # Send command response
                        send_reply(service, msg_data, sender, command_result['subject'], command_result['body'])
                        logger.info(f"Sent command response for: {command_result['command']}")
                    else:
                        # Send error response
                        error_body = f"Error: {command_result['error']}\n\nSend 'Vertigo: Help' for available commands."
                        send_reply(service, msg_data, sender, "Vertigo: Error", error_body)
                        logger.error(f"Command error: {command_result['error']}")
                        
                elif is_status_request(subject, body):
                    process_status_request(service, msg_data, subject, body, sender)
                elif is_daily_summary_request(subject, body):
                    process_daily_summary(service, msg_data, subject, body, sender)
                else:
                    process_meeting_transcript(service, msg_data, subject, body, sender)
                
                # Mark as read
                service.users().messages().modify(
                    userId='me',
                    id=msg_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                logger.info("Marked email as read.")
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing message {msg_id}: {e}")
                continue
        
        # Update trace with success
        langfuse_client.update_trace(
            trace_id=trace_id,
            metadata={
                "processed_count": processed_count,
                "total_messages": len(messages),
                "success": True
            },
            output={
                "processed_count": processed_count,
                "total_messages": len(messages)
            },
            level="DEFAULT"
        )
        
        # Flush traces
        langfuse_client.flush()
        
        return {
            "processed_count": processed_count,
            "total_messages": len(messages),
            "status": "success",
            "trace_id": trace_id
        }
        
    except Exception as e:
        logger.error(f"Error in process_unread_emails: {e}")
        
        # Update trace with error
        langfuse_client.update_trace(
            trace_id=trace_id,
            metadata={"error": str(e), "success": False},
            level="ERROR"
        )
        langfuse_client.flush()
        
        return {
            "error": str(e),
            "status": "error",
            "trace_id": trace_id
        }

@functions_framework.http
def email_processor_v2(request):
    """Cloud Function entry point."""
    logger.info("Email processor function triggered.")
    
    # Create entry point traces for both systems
    entry_trace_id = langfuse_client.create_trace(
        name="email_processor_v2",
        metadata={
            "operation": "cloud_function_entry",
            "service": "email-processor",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # Create Langwatch trace for demo
    langwatch_trace_id = langwatch_client.create_trace(
        name="vertigo_email_processor",
        input_data="Vertigo email processing system triggered",
        metadata={
            "system": "vertigo",
            "service": "email-processor-v2",
            "user_id": "vertigo_system",
            "demo": "langwatch_cto_demo"
        }
    )
    
    try:
        # Check if this is an automatic daily summary request
        if request and request.get_json():
            request_data = request.get_json()
            action = request_data.get('action')
            
            if action == 'generate_daily_summary':
                recipient = request_data.get('recipient', 'sdulaney@mergeworld.com')
                logger.info(f"Generating automatic daily summary for {recipient}")
                
                # Update trace for daily summary operation
                langfuse_client.update_trace(
                    trace_id=entry_trace_id,
                    metadata={
                        "action": "generate_daily_summary",
                        "recipient": recipient
                    }
                )
                
                result = generate_automatic_daily_summary(recipient)
                langfuse_client.flush()
                return (result, 200, {"Content-Type": "application/json"})
        
        # Default behavior: process unread emails
        result = process_unread_emails()
        
        # Update entry trace with success
        langfuse_client.update_trace(
            trace_id=entry_trace_id,
            metadata={"success": True, "action": "process_unread_emails"},
            level="DEFAULT"
        )
        langfuse_client.flush()
        
        return (result, 200, {"Content-Type": "application/json"})
    except Exception as e:
        logger.error(f"Function error: {e}")
        
        # Update entry trace with error
        langfuse_client.update_trace(
            trace_id=entry_trace_id,
            metadata={"error": str(e), "success": False},
            level="ERROR"
        )
        langfuse_client.flush()
        
        return ({"error": str(e), "status": "error", "trace_id": entry_trace_id}, 500, {"Content-Type": "application/json"}) 