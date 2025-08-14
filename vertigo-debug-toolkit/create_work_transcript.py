#!/usr/bin/env python3
"""
Create and send work transcript to Vertigo agent.

This script creates a comprehensive transcript of today's work on the Vertigo Debug Toolkit
and sends it to vertigo.agent.2025@gmail.com for processing and inclusion in the 3:00 PM summary.
"""

import json
import os
import sys
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.cloud import secretmanager
import base64
from email.mime.text import MIMEText

class WorkTranscriptSender:
    def __init__(self):
        self.project_id = "vertigo-466116"
        self.gmail_address = "vertigo.agent.2025@gmail.com"
        self.sender_email = "sdulaney@mergeworld.com"  # Your email
        
    def get_gmail_service(self):
        """Get Gmail service with OAuth credentials."""
        try:
            # Get OAuth token from Secret Manager
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{self.project_id}/secrets/gmail-oauth-token/versions/latest"
            response = client.access_secret_version(request={"name": secret_name})
            token_data = json.loads(response.payload.data.decode("UTF-8"))
            
            # Create credentials
            creds = Credentials.from_authorized_user_info(token_data)
            service = build('gmail', 'v1', credentials=creds)
            return service
        except Exception as e:
            print(f"❌ Error getting Gmail service: {e}")
            return None
    
    def create_work_transcript(self):
        """Create a comprehensive transcript of today's work."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        transcript = f"""
# Vertigo Debug Toolkit Development Session - {today}

## Executive Summary
Today's session focused on diagnosing and fixing critical issues with the Vertigo email processing system, enhancing the Vertigo Debug Toolkit with comprehensive cloud monitoring capabilities, and ensuring stable operation of all Vertigo cloud services.

## Key Accomplishments

### 1. Email Processor Issue Resolution
**Problem Identified**: The Vertigo email processor stopped processing emails automatically, leaving 3 unread messages in vertigo.agent.2025@gmail.com inbox.

**Root Cause Analysis**: 
- Discovered that the Cloud Scheduler job was calling the wrong function URL
- Original URL: https://us-central1-vertigo-466116.cloudfunctions.net/email-processor (with hyphen)
- Correct URL: https://us-central1-vertigo-466116.cloudfunctions.net/email_processor (with underscore)

**Solution Implemented**:
- Fixed the Cloud Scheduler job URL to point to the correct function endpoint
- Verified the 10-minute polling strategy is working correctly
- Confirmed all unread emails were processed successfully

**Result**: Email processor is now functioning normally, processing emails every 10 minutes as originally designed.

### 2. Vertigo Debug Toolkit Enhancements
**New Features Added**:

#### Cloud Service Monitoring System
- Created comprehensive CloudServiceMonitor class for real-time health checks
- Implemented monitoring for all Vertigo cloud functions:
  - Email Processor (email_processor)
  - Meeting Processor v2 (meeting_processor_v2) 
  - Status Generator (status_generator)
- Added response time tracking and error detection
- Integrated with dashboard for real-time status display

#### Enhanced Dashboard Capabilities
- Updated "Vertigo Status" button to check actual cloud services instead of local health
- Added detailed service status reporting with individual function health
- Implemented testing capabilities for email and meeting processors
- Added deployment information display

#### Diagnostic Tools
- Created email_processor_diagnostic.py for comprehensive troubleshooting
- Built Gmail API integration testing
- Added OAuth token validation
- Implemented push notification setup scripts

### 3. Technical Infrastructure Improvements
**Flask Application Enhancements**:
- Fixed missing Jinja2 templates (admin_users.html, profile.html, edit_profile.html, change_password.html)
- Added comprehensive error handling and logging
- Implemented proper authentication flows
- Enhanced user management interface

**Development Environment**:
- Set up proper Git version control
- Created comprehensive documentation
- Added Docker support for containerized deployment
- Implemented proper dependency management

### 4. Cloud Service Architecture
**Current Deployed Services**:
1. **Email Processor** (email_processor)
   - Function: Processes incoming emails every 10 minutes
   - Status: ✅ Operational
   - Trigger: Cloud Scheduler (every 10 minutes)

2. **Meeting Processor v2** (meeting_processor_v2)
   - Function: Processes meeting transcripts and extracts key information
   - Status: ✅ Operational
   - Trigger: HTTP endpoint

3. **Status Generator** (status_generator)
   - Function: Generates executive status updates
   - Status: ✅ Operational
   - Trigger: HTTP endpoint

## Technical Details

### Cloud Function URLs
- Email Processor: https://us-central1-vertigo-466116.cloudfunctions.net/email_processor
- Meeting Processor: https://us-central1-vertigo-466116.cloudfunctions.net/meeting_processor_v2
- Status Generator: https://us-central1-vertigo-466116.cloudfunctions.net/status_generator

### Monitoring Integration
- Real-time health checks via CloudServiceMonitor
- Dashboard integration for operational visibility
- Automated testing capabilities
- Comprehensive logging and error tracking

### Security & Authentication
- OAuth token management via Google Secret Manager
- Secure Gmail API integration
- Proper service account permissions
- Environment variable management

## Business Impact

### Operational Stability
- Restored automatic email processing functionality
- Ensured continuous operation of Vertigo agent
- Implemented proactive monitoring to prevent future outages

### Development Velocity
- Enhanced debugging capabilities with comprehensive toolkit
- Improved visibility into cloud service health
- Streamlined troubleshooting processes

### Quality Assurance
- Added comprehensive testing capabilities
- Implemented real-time monitoring
- Enhanced error detection and reporting

## Next Steps & Recommendations

### Immediate Actions
1. Monitor email processing for the next 24 hours to ensure stability
2. Test the enhanced dashboard monitoring features
3. Validate all cloud service integrations

### Future Enhancements
1. Implement automated alerting for service outages
2. Add performance metrics and analytics
3. Enhance the debug toolkit with additional diagnostic capabilities
4. Consider implementing automated recovery procedures

### Maintenance Schedule
- Weekly health check reviews
- Monthly security token refresh
- Quarterly architecture reviews

## Conclusion

Today's session successfully resolved critical operational issues and significantly enhanced the Vertigo Debug Toolkit's capabilities. The email processing system is now stable and operational, and the monitoring infrastructure provides comprehensive visibility into all Vertigo cloud services. The enhanced toolkit will improve development velocity and operational reliability going forward.

**Session Duration**: Full day development session
**Participants**: Stephen Dulaney (Developer), AI Assistant (Development Partner)
**Status**: ✅ All objectives completed successfully
**Impact**: High - Restored critical functionality and enhanced operational capabilities

---
*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*Vertigo Debug Toolkit Development Session*
        """
        
        return transcript.strip()
    
    def send_transcript_email(self, transcript):
        """Send the work transcript to the Vertigo agent."""
        service = self.get_gmail_service()
        if not service:
            print("❌ Failed to get Gmail service")
            return False
        
        try:
            # Create email message
            subject = f"Work Transcript - Vertigo Debug Toolkit Development Session - {datetime.now().strftime('%Y-%m-%d')}"
            
            message = MIMEText(transcript, 'plain')
            message['to'] = self.gmail_address
            message['from'] = self.sender_email
            message['subject'] = subject
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the email
            print(f"📧 Sending work transcript to {self.gmail_address}...")
            print(f"📋 Subject: {subject}")
            
            service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            
            print("✅ Work transcript sent successfully!")
            print("📋 The Vertigo agent will process this transcript and include it in the 3:00 PM summary if merited.")
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def run(self):
        """Run the complete transcript creation and sending process."""
        print("🚀 Creating and sending work transcript to Vertigo agent...")
        print(f"📧 Target: {self.gmail_address}")
        print(f"⏰ Timestamp: {datetime.now().isoformat()}")
        
        # Create transcript
        print("\n📝 Creating work transcript...")
        transcript = self.create_work_transcript()
        
        # Send email
        print("\n📧 Sending transcript...")
        success = self.send_transcript_email(transcript)
        
        if success:
            print(f"\n🎉 Work transcript sent successfully!")
            print(f"📋 The transcript will be processed by the Vertigo agent and may appear in your 3:00 PM summary.")
        else:
            print(f"\n❌ Failed to send work transcript.")
            return False
        
        return True

def main():
    """Main function."""
    sender = WorkTranscriptSender()
    success = sender.run()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 