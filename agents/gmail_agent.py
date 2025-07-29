"""
Gmail Agent implementation using Vertex AI.
Demonstrates integration with Google Workspace APIs.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from config.auth import auth
from config.settings import settings
from .base_agent import BaseAgent
import os
from gemini.configure import configure_gemini
configure_gemini()

class GmailAgent(BaseAgent):
    """
    Gmail integration agent using Vertex AI.
    Can read, analyze, and respond to emails.
    """
    
    def __init__(self, name: str = "Gmail Assistant"):
        super().__init__(
            name=name,
            description="An AI assistant that can help with Gmail operations including reading, analyzing, and drafting emails."
        )
        
        # Gmail API setup
        self.gmail_service = None
        self._setup_gmail_service()
        
        # Override capabilities
        self.capabilities.update({
            "gmail_integration": True,
            "email_analysis": True,
            "email_drafting": True,
            "email_search": True,
        })
    
    def _setup_gmail_service(self):
        """Set up Gmail API service."""
        try:
            # Gmail API scopes
            SCOPES = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.compose',
                'https://www.googleapis.com/auth/gmail.modify'
            ]
            
            creds = None
            
            # Try to load credentials from file
            if settings.gmail_credentials_path and os.path.exists(settings.gmail_credentials_path):
                creds = Credentials.from_authorized_user_file(
                    settings.gmail_credentials_path, SCOPES
                )
            
            # If no valid credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to set up Gmail service: {e}")
            self.gmail_service = None
    
    async def get_recent_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get recent emails from Gmail."""
        if not self.gmail_service:
            return []
        
        try:
            # Get recent messages
            results = self.gmail_service.users().messages().list(
                userId='me', maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.gmail_service.users().messages().get(
                    userId='me', id=message['id']
                ).execute()
                
                # Extract email details
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                
                emails.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'snippet': msg.get('snippet', ''),
                    'threadId': msg.get('threadId', '')
                })
            
            return emails
            
        except Exception as e:
            self.logger.error(f"Error fetching emails: {e}")
            return []
    
    async def analyze_email_content(self, email_id: str) -> Dict[str, Any]:
        """Analyze the content of a specific email."""
        if not self.gmail_service:
            return {"error": "Gmail service not available"}
        
        try:
            # Get full message
            msg = self.gmail_service.users().messages().get(
                userId='me', id=email_id, format='full'
            ).execute()
            
            # Extract content
            content = self._extract_email_content(msg)
            
            # Use Gemini to analyze the email
            analysis_prompt = f"""
            Analyze this email and provide insights:
            
            Email Content:
            {content}
            
            Please provide:
            1. Key topics discussed
            2. Sentiment analysis
            3. Action items or requests
            4. Priority level (high/medium/low)
            5. Suggested response approach
            """
            
            response = self.model.generate_content(analysis_prompt)
            
            return {
                "email_id": email_id,
                "content": content,
                "analysis": response.text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing email: {e}")
            return {"error": str(e)}
    
    def _extract_email_content(self, msg: Dict[str, Any]) -> str:
        """Extract readable content from Gmail message."""
        try:
            payload = msg['payload']
            
            # Handle multipart messages
            if 'parts' in payload:
                content = ""
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        content += part['body'].get('data', '')
                return content
            
            # Handle simple messages
            elif 'body' in payload:
                return payload['body'].get('data', '')
            
            return "No readable content found"
            
        except Exception as e:
            self.logger.error(f"Error extracting email content: {e}")
            return "Error extracting content"
    
    async def draft_email_response(self, email_id: str, response_type: str = "professional") -> str:
        """Draft a response to an email using Gemini."""
        if not self.gmail_service:
            return "Gmail service not available"
        
        try:
            # Get original email
            msg = self.gmail_service.users().messages().get(
                userId='me', id=email_id, format='full'
            ).execute()
            
            content = self._extract_email_content(msg)
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Re: Email')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            
            # Generate response using Gemini
            response_prompt = f"""
            Draft a {response_type} email response to this message:
            
            From: {sender}
            Subject: {subject}
            Content: {content}
            
            Please write a professional, helpful response that:
            1. Addresses the key points in the original email
            2. Maintains a {response_type} tone
            3. Is concise but complete
            4. Includes appropriate greetings and closings
            """
            
            response = self.model.generate_content(response_prompt)
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error drafting email response: {e}")
            return f"Error drafting response: {str(e)}"
    
    async def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search emails using Gmail API."""
        if not self.gmail_service:
            return []
        
        try:
            results = self.gmail_service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = self.gmail_service.users().messages().get(
                    userId='me', id=message['id']
                ).execute()
                
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                
                emails.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'snippet': msg.get('snippet', ''),
                    'threadId': msg.get('threadId', '')
                })
            
            return emails
            
        except Exception as e:
            self.logger.error(f"Error searching emails: {e}")
            return []
    
    async def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhanced chat method with Gmail-specific capabilities."""
        # Check for Gmail-specific commands
        if "recent emails" in message.lower() or "latest emails" in message.lower():
            emails = await self.get_recent_emails(5)
            if emails:
                email_list = "\n".join([
                    f"- {email['subject']} (from {email['sender']})"
                    for email in emails
                ])
                return f"Here are your recent emails:\n{email_list}"
            else:
                return "No recent emails found or Gmail service not available."
        
        elif "analyze email" in message.lower():
            # Extract email ID from message or use the most recent
            emails = await self.get_recent_emails(1)
            if emails:
                analysis = await self.analyze_email_content(emails[0]['id'])
                return f"Email Analysis:\n{analysis.get('analysis', 'Analysis failed')}"
            else:
                return "No emails found to analyze."
        
        elif "draft response" in message.lower():
            emails = await self.get_recent_emails(1)
            if emails:
                response = await self.draft_email_response(emails[0]['id'])
                return f"Drafted Response:\n\n{response}"
            else:
                return "No emails found to respond to."
        
        # Fall back to base chat method
        return await super().chat(message, context)


# Example usage
async def main():
    """Example usage of the GmailAgent."""
    agent = GmailAgent()
    
    # Test basic functionality
    response = await agent.chat("What can you help me with regarding emails?")
    print(f"Agent: {response}")
    
    # Test email retrieval (if Gmail is set up)
    response = await agent.chat("Show me my recent emails")
    print(f"Agent: {response}")


if __name__ == "__main__":
    asyncio.run(main()) 