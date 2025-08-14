from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import email

# Load credentials
creds = Credentials.from_authorized_user_file('token.json', [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
])
service = build('gmail', 'v1', credentials=creds)

# Get unread messages
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

    # Get the email body
    if 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    else:
        # If multipart, get the first part
        parts = payload.get('parts', [])
        body = ''
        for part in parts:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
    print(f"Body:\n{body}")

    # (Optional) Mark as read
    # service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
