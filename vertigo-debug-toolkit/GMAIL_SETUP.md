
# Gmail API Setup for Vertigo

## 1. Enable Gmail API
- Go to Google Cloud Console
- Navigate to APIs & Services > Library
- Search for "Gmail API" and enable it

## 2. Create Service Account
- Go to IAM & Admin > Service Accounts
- Create new service account: "vertigo-gmail-processor"
- Grant "Gmail API" permissions

## 3. Set up Domain-Wide Delegation
- Download service account key
- In Google Workspace Admin:
  - Go to Security > API Controls > Domain-wide Delegation
  - Add client ID and scope: https://www.googleapis.com/auth/gmail.readonly

## 4. Update Environment Variables
- Set GMAIL_CREDENTIALS_PATH to your service account key file
- Ensure GOOGLE_CLOUD_PROJECT_ID is set

## 5. Test Gmail Connection
- Run: python test_gmail_connection.py
