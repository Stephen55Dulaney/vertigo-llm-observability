from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import requests
import email

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

        # Send to meeting processor
        payload_json = {
            "transcript": body,
            "transcript_type": "dictation",
            "project": "vertigo",  # You can make this dynamic later
            "participants": [],
            "duration_minutes": 45,
            "meeting_title": subject
        }
        response = requests.post(meeting_processor_url, json=payload_json)
        print("Meeting processor response:", response.json())

        # Mark as read
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        print("Marked email as read.")

if __name__ == "__main__":
    process_unread_emails() 