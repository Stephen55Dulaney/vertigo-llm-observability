#!/usr/bin/env python3
"""
Send test emails to trigger Vertigo email processing and generate Langfuse traces.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

def send_test_email(subject, body, to_email="sdulaney@mergeworld.com"):
    """Send a test email through Gmail SMTP."""
    
    # Gmail SMTP configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    # You'll need to use your actual Gmail credentials or an app password
    from_email = "sdulaney@mergeworld.com"
    
    print(f"📧 Sending test email...")
    print(f"   Subject: {subject}")
    print(f"   To: {to_email}")
    print(f"   Body preview: {body[:100]}...")
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Note: This would require Gmail app password setup
        # For now, let's just print what would be sent
        print("🚨 Note: Actually sending email requires Gmail app password setup")
        print("📧 Would send this email:")
        print("=" * 50)
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def create_test_emails():
    """Create various test emails to trigger different Langfuse traces."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    test_emails = [
        {
            "subject": "Vertigo: Help",
            "body": "Please send me the help information for available commands."
        },
        {
            "subject": "Meeting Notes - Vertigo Sprint Planning",
            "body": f"""Meeting transcript from {timestamp}:

We discussed the LLM observability implementation for Vertigo. Key points:

1. Langfuse integration is working in the debug toolkit
2. Need to verify cloud functions are generating traces  
3. Planning to test different prompt variants for meeting processing
4. Discussion about A/B testing framework for prompt optimization

Action items:
- Complete Langfuse tracing in email processor
- Test meeting processor with new prompt variants
- Set up daily summary automation

Next meeting scheduled for tomorrow at 10 AM.
"""
        },
        {
            "subject": "3:00 PM Daily Summary - Vertigo",
            "body": f"""Daily update for {timestamp}:

Today's Ambition:
Complete Langfuse integration across all Vertigo cloud functions and generate comprehensive traces for observability.

What We Did Today:
- Fixed Langfuse secret configuration in Google Cloud Secret Manager
- Updated email processor to generate traces for email processing operations
- Tested cloud function deployment and verified email processing functionality
- Created separate secrets for langfuse-public-key and langfuse-secret-key

What We'll Do Next:
- Verify Langfuse traces are appearing in dashboard
- Test different types of email processing (help commands, meeting notes, status requests)
- Implement trace monitoring and performance optimization
- Document the complete observability setup for team use

Status: Making good progress on observability implementation.
"""
        }
    ]
    
    for i, email_data in enumerate(test_emails, 1):
        print(f"\n🔄 Test Email {i}:")
        send_test_email(email_data["subject"], email_data["body"])

if __name__ == "__main__":
    print("🚀 Creating test emails to trigger Vertigo processing...")
    create_test_emails()
    print("\n✅ Test emails prepared!")
    print("\n📋 Next steps:")
    print("1. Actually send these emails to sdulaney@mergeworld.com")
    print("2. Wait for cloud function to process them")  
    print("3. Check Langfuse dashboard for new traces")
    print("4. Monitor cloud function logs for any issues")