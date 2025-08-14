import os
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.send']

def main():
    creds = None
    flow = InstalledAppFlow.from_client_secrets_file(
        '/Users/stephendulaney/Documents/KeyStorage/client_secret_579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com.json', SCOPES)  # <-- Replace with your downloaded file
    creds = flow.run_local_server(port=8080)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("Authorization complete! token.json saved.")

if __name__ == '__main__':
    main()