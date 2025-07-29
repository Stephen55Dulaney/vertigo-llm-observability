#!/usr/bin/env python3
"""
Daily Cursor Meeting Summarizer
Generates meeting summaries from workspace activity and emails them daily at 5 PM CST.
"""

import os
import sys
import json
import subprocess
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import base64

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]

class CursorMeetingSummarizer:
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = workspace_path
        self.gmail_service = None
        self.recipients = {
            'to': 'verigo.agent.2025@gmail.com',
            'cc': 'stephen.dulaney@gmail.com'
        }
        self._setup_gmail_service()
        self._setup_gemini()
    
    def _setup_gmail_service(self):
        """Set up Gmail API service."""
        try:
            creds = None
            token_path = 'token.json'
            
            # Load existing token
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # You'll need to set up OAuth2 credentials
                    credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
                    if os.path.exists(credentials_path):
                        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                        creds = flow.run_local_server(port=0)
                    else:
                        print("Warning: Gmail credentials not found. Email functionality disabled.")
                        return
                
                # Save credentials for next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            print("✅ Gmail service initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize Gmail service: {e}")
            self.gmail_service = None
    
    def _setup_gemini(self):
        """Set up Gemini AI for content generation."""
        try:
            # Configure Gemini
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-pro')
                print("✅ Gemini AI configured")
            else:
                print("Warning: GEMINI_API_KEY not found. Using fallback summary generation.")
                self.model = None
        except Exception as e:
            print(f"❌ Failed to configure Gemini: {e}")
            self.model = None
    
    def get_git_activity(self, since_date: str) -> Dict[str, Any]:
        """Get git activity since the specified date."""
        try:
            os.chdir(self.workspace_path)
            
            # Get commits since date
            cmd = f'git log --since="{since_date}" --pretty=format:"%h|%an|%ad|%s" --date=short'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            commits = []
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
            
            # Get file changes
            cmd = f'git diff --name-status --since="{since_date}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            file_changes = []
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('\t', 1)
                        if len(parts) == 2:
                            file_changes.append({
                                'status': parts[0],
                                'file': parts[1]
                            })
            
            # Get current branch
            cmd = 'git branch --show-current'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            current_branch = result.stdout.strip() if result.returncode == 0 else "main"
            
            return {
                'commits': commits,
                'file_changes': file_changes,
                'current_branch': current_branch,
                'total_commits': len(commits),
                'total_files_changed': len(file_changes)
            }
            
        except Exception as e:
            print(f"Error getting git activity: {e}")
            return {'commits': [], 'file_changes': [], 'current_branch': 'main', 'total_commits': 0, 'total_files_changed': 0}
    
    def get_workspace_activity(self) -> Dict[str, Any]:
        """Get recent workspace activity and file modifications."""
        try:
            os.chdir(self.workspace_path)
            
            # Get recently modified files (last 24 hours)
            cmd = 'find . -type f -mtime -1 -not -path "./.git/*" | head -20'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            recent_files = []
            if result.returncode == 0:
                recent_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            
            # Get project structure overview
            cmd = 'find . -maxdepth 2 -type f -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.md" -o -name "*.json" | head -15'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            project_files = []
            if result.returncode == 0:
                project_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            
            # Get TODO/FIXME comments
            cmd = 'grep -r -n -E "(TODO|FIXME|NOTE)" --include="*.py" --include="*.js" --include="*.ts" . | head -10'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            todos = []
            if result.returncode == 0:
                todos = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            return {
                'recent_files': recent_files,
                'project_files': project_files,
                'todos': todos,
                'workspace_path': self.workspace_path
            }
            
        except Exception as e:
            print(f"Error getting workspace activity: {e}")
            return {'recent_files': [], 'project_files': [], 'todos': [], 'workspace_path': self.workspace_path}
    
    def generate_summary_with_ai(self, git_data: Dict, workspace_data: Dict) -> str:
        """Generate meeting summary using AI."""
        if not self.model:
            return self._generate_fallback_summary(git_data, workspace_data)
        
        try:
            prompt = f"""
            Generate a professional meeting summary based on the following workspace activity data:

            GIT ACTIVITY:
            - Total commits: {git_data['total_commits']}
            - Current branch: {git_data['current_branch']}
            - Recent commits: {json.dumps(git_data['commits'][:5], indent=2)}
            - Files changed: {git_data['total_files_changed']}

            WORKSPACE ACTIVITY:
            - Recent files modified: {workspace_data['recent_files'][:10]}
            - Project files: {workspace_data['project_files'][:10]}
            - TODOs/Notes found: {workspace_data['todos'][:5]}

            Please generate a meeting summary that includes:
            1. **Today's Accomplishments** - What was worked on today
            2. **Key Changes Made** - Important commits and file changes
            3. **Current Status** - Where things stand
            4. **Next Steps** - What should be worked on next based on TODOs and recent activity
            5. **Technical Notes** - Any important technical details

            Format the response as a professional meeting summary suitable for email.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"Error generating AI summary: {e}")
            return self._generate_fallback_summary(git_data, workspace_data)
    
    def _generate_fallback_summary(self, git_data: Dict, workspace_data: Dict) -> str:
        """Generate a basic summary without AI."""
        today = datetime.now().strftime("%B %d, %Y")
        
        summary = f"""
# Daily Development Summary - {today}

## Today's Activity Overview
- **Total Commits**: {git_data['total_commits']}
- **Current Branch**: {git_data['current_branch']}
- **Files Modified**: {git_data['total_files_changed']}
- **Recent Files Worked On**: {len(workspace_data['recent_files'])}

## Recent Commits
"""
        
        for commit in git_data['commits'][:5]:
            summary += f"- **{commit['hash']}** by {commit['author']} on {commit['date']}: {commit['message']}\n"
        
        if workspace_data['recent_files']:
            summary += "\n## Recently Modified Files\n"
            for file in workspace_data['recent_files'][:10]:
                summary += f"- {file}\n"
        
        if workspace_data['todos']:
            summary += "\n## Outstanding TODOs/Notes\n"
            for todo in workspace_data['todos'][:5]:
                summary += f"- {todo}\n"
        
        summary += f"""
## Next Steps
Based on recent activity, continue working on:
1. Address any outstanding TODOs
2. Complete features in progress on branch: {git_data['current_branch']}
3. Review and test recent changes

---
*This summary was automatically generated from workspace activity.*
"""
        
        return summary
    
    def send_email_summary(self, summary: str) -> bool:
        """Send the meeting summary via email."""
        if not self.gmail_service:
            print("Gmail service not available. Saving summary to file instead.")
            self._save_summary_to_file(summary)
            return False
        
        try:
            today = datetime.now().strftime("%B %d, %Y")
            subject = f"Daily Cursor Development Summary - {today}"
            
            # Create message
            message = MIMEMultipart()
            message['to'] = self.recipients['to']
            message['cc'] = self.recipients['cc']
            message['subject'] = subject
            
            # Add body
            message.attach(MIMEText(summary, 'plain'))
            
            # Send message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"✅ Email sent successfully! Message ID: {send_message['id']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            print("Saving summary to file instead.")
            self._save_summary_to_file(summary)
            return False
    
    def _save_summary_to_file(self, summary: str):
        """Save summary to a file as backup."""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"meeting_summary_{today}.md"
        
        try:
            with open(filename, 'w') as f:
                f.write(summary)
            print(f"✅ Summary saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save summary: {e}")
    
    def generate_and_send_daily_summary(self):
        """Generate and send the daily meeting summary."""
        print("🚀 Starting daily meeting summary generation...")
        
        # Get yesterday's date for git activity
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Collect data
        print("📊 Collecting git activity...")
        git_data = self.get_git_activity(yesterday)
        
        print("📁 Collecting workspace activity...")
        workspace_data = self.get_workspace_activity()
        
        # Generate summary
        print("🤖 Generating summary...")
        summary = self.generate_summary_with_ai(git_data, workspace_data)
        
        # Send email
        print("📧 Sending email...")
        success = self.send_email_summary(summary)
        
        if success:
            print("✅ Daily summary completed successfully!")
        else:
            print("⚠️ Summary generated but email failed. Check saved file.")
        
        return summary

def main():
    """Main entry point."""
    summarizer = CursorMeetingSummarizer()
    summary = summarizer.generate_and_send_daily_summary()
    print("\n" + "="*50)
    print("GENERATED SUMMARY:")
    print("="*50)
    print(summary)

if __name__ == "__main__":
    main()