from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import requests
import email
from email.mime.text import MIMEText

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

# Load credentials
creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('gmail', 'v1', credentials=creds)

# Meeting processor endpoint
meeting_processor_url = "https://us-central1-vertigo-466116.cloudfunctions.net/meeting-processor"

PROJECTS = ['vertigo', 'memento', 'gemino']

def get_email_body(payload):
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
    text = (subject + " " + body).lower()
    for project in PROJECTS:
        if project in text:
            return project
    return "unknown"

def send_reply(service, original_msg, to_email, subject, body_text):
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
    print(f"Sent auto-reply to {to_email}")

def process_unread_emails():
    results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD']).execute()
    messages = results.get('messages', [])
    print(f'Found {len(messages)} unread messages.')

    for msg in messages:
        msg_id = msg['id']
        msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = msg_data['payload']
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '(No Sender)')
        print(f"\nSubject: {subject}\nFrom: {sender}")

        body = get_email_body(payload)
        print(f"Body:\n{body}")

        # Detect project
        project = detect_project(subject, body)
        print(f"Detected project: {project}")

        # Send to meeting processor
        payload_json = {
            "transcript": body,
            "transcript_type": "dictation",
            "project": project,
            "participants": [],
            "duration_minutes": 45,
            "meeting_title": subject
        }
        response = requests.post(meeting_processor_url, json=payload_json)
        resp_json = response.json()
        print("Meeting processor response:", resp_json)

        # Auto-reply with meeting notes
        meeting_notes = resp_json.get('processed_notes', '')
        sender_email = email.utils.parseaddr(sender)[1]
        send_reply(service, msg_data, sender_email, subject, meeting_notes)

        # Mark as read
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        print("Marked email as read.")

if __name__ == "__main__":
    process_unread_emails() 