#!/usr/bin/env python3
"""
Gmail Monitoring Service for Vertigo Debug Toolkit

This service monitors Gmail for unread emails and triggers alerts when emails
are not processed within a reasonable timeframe.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GmailMonitoringResult:
    """Result of Gmail monitoring check."""
    unread_count: int
    oldest_unread_age_minutes: float
    emails_summary: List[Dict]
    alert_triggered: bool
    error_message: Optional[str] = None

class GmailMonitoringService:
    """Monitors Gmail for unread emails and triggers alerts."""
    
    def __init__(self):
        self.gmail_address = "vertigo.agent.2025@gmail.com"
        self.alert_threshold_minutes = 15  # Alert if emails unread for 15+ minutes
        self.max_unread_threshold = 3     # Alert if 3+ emails unread
        
    def simulate_gmail_check(self) -> GmailMonitoringResult:
        """
        Simulate Gmail monitoring check.
        In production, this would use Gmail API to check for unread emails.
        """
        # Based on the screenshot, we have 5 unread emails from today
        simulated_unread_emails = [
            {
                "subject": "Fwd: Notes: 'AI Garage Virtual Office' Aug 12, 2025",
                "sender": "Stephen Dulaney",
                "received_time": datetime.now() - timedelta(hours=2, minutes=30),
                "body_preview": "Stephen Dulaney Agentic Systems Architect MERGE..."
            },
            {
                "subject": "Fwd: Notes: 'AI Garage Virtual Office' Aug 12, 2025", 
                "sender": "Stephen Dulaney",
                "received_time": datetime.now() - timedelta(hours=2, minutes=25),
                "body_preview": "Stephen Dulaney Agentic Systems Architect MERGE..."
            },
            {
                "subject": "Fwd: Notes: 'Jay / Stephen - Project Review for Github checkin candidate' Aug 12, 2025",
                "sender": "Stephen Dulaney", 
                "received_time": datetime.now() - timedelta(hours=13, minutes=45),
                "body_preview": "Forwarded message from Jay..."
            },
            {
                "subject": "Fwd: Notes: 'Morning Check-In: Daily Ambition Round-Robin' Aug 12, 2025",
                "sender": "Stephen Dulaney",
                "received_time": datetime.now() - timedelta(hours=14, minutes=30),
                "body_preview": "Forwarded message..."
            },
            {
                "subject": "Fwd: Notes: 'AI Garage Virtual Office' Aug 11, 2025",
                "sender": "Stephen Dulaney",
                "received_time": datetime.now() - timedelta(days=1, hours=2),
                "body_preview": "Forwarded message from Gemini..."
            }
        ]
        
        unread_count = len(simulated_unread_emails)
        
        # Calculate oldest unread email age
        oldest_email = min(simulated_unread_emails, key=lambda x: x['received_time'])
        oldest_age_minutes = (datetime.now() - oldest_email['received_time']).total_seconds() / 60
        
        # Determine if alert should be triggered
        alert_triggered = (
            unread_count >= self.max_unread_threshold or 
            oldest_age_minutes >= self.alert_threshold_minutes
        )
        
        emails_summary = [
            {
                "subject": email["subject"][:50] + "..." if len(email["subject"]) > 50 else email["subject"],
                "sender": email["sender"],
                "age_hours": round((datetime.now() - email['received_time']).total_seconds() / 3600, 1),
                "preview": email["body_preview"][:100] + "..." if len(email["body_preview"]) > 100 else email["body_preview"]
            }
            for email in simulated_unread_emails
        ]
        
        return GmailMonitoringResult(
            unread_count=unread_count,
            oldest_unread_age_minutes=oldest_age_minutes,
            emails_summary=emails_summary,
            alert_triggered=alert_triggered
        )
    
    def check_oauth_token_status(self) -> Dict[str, any]:
        """Check if Gmail OAuth token is valid."""
        # Based on the error we saw, the token is expired
        return {
            "status": "expired",
            "error": "Token has been expired or revoked",
            "last_refresh_attempt": datetime.now() - timedelta(minutes=5),
            "needs_renewal": True
        }
    
    def generate_alert_message(self, monitoring_result: GmailMonitoringResult, token_status: Dict) -> str:
        """Generate comprehensive alert message."""
        alert_parts = []
        
        # Unread emails alert
        if monitoring_result.unread_count > 0:
            alert_parts.append(f"📧 {monitoring_result.unread_count} unread emails in {self.gmail_address}")
            alert_parts.append(f"⏰ Oldest unread email: {monitoring_result.oldest_unread_age_minutes:.1f} minutes ago")
        
        # OAuth token issue
        if token_status["status"] == "expired":
            alert_parts.append(f"🔑 Gmail OAuth token has expired - emails cannot be processed automatically")
            alert_parts.append(f"❗ Token renewal required for email processing automation")
        
        # Email processing status
        alert_parts.append(f"🔧 Email Processor Cloud Function: Healthy (but cannot access Gmail)")
        alert_parts.append(f"⚠️ Automatic email processing: DISABLED due to authentication issue")
        
        return "\\n".join(alert_parts)

def run_gmail_monitoring_demo():
    """Demonstrate how Gmail monitoring should work."""
    print("🔍 GMAIL MONITORING SYSTEM DEMONSTRATION")
    print("=" * 60)
    print("This shows what our monitoring system SHOULD have detected...")
    print()
    
    service = GmailMonitoringService()
    
    # Check Gmail status
    print("1️⃣ CHECKING GMAIL INBOX...")
    monitoring_result = service.simulate_gmail_check()
    
    print(f"   📊 Unread emails: {monitoring_result.unread_count}")
    print(f"   ⏰ Oldest unread: {monitoring_result.oldest_unread_age_minutes:.1f} minutes ago")
    print(f"   🚨 Alert triggered: {'YES' if monitoring_result.alert_triggered else 'NO'}")
    print()
    
    # Check OAuth token
    print("2️⃣ CHECKING GMAIL API ACCESS...")
    token_status = service.check_oauth_token_status()
    print(f"   🔑 OAuth token status: {token_status['status'].upper()}")
    print(f"   ❗ Error: {token_status['error']}")
    print()
    
    # Show what emails are waiting
    print("3️⃣ UNPROCESSED EMAILS:")
    for i, email in enumerate(monitoring_result.emails_summary, 1):
        print(f"   {i}. [{email['age_hours']}h ago] {email['subject']}")
        print(f"      From: {email['sender']}")
        print(f"      Preview: {email['preview']}")
        print()
    
    # Generate alert message
    print("4️⃣ ALERT MESSAGE (should have been sent to sdulaney@mergeworld.com):")
    alert_message = service.generate_alert_message(monitoring_result, token_status)
    print("   " + alert_message.replace("\\n", "\\n   "))
    print()
    
    # Recommendations
    print("5️⃣ RECOMMENDED ACTIONS:")
    print("   ✅ Renew Gmail OAuth token (highest priority)")
    print("   ✅ Process the 5 unread emails manually")
    print("   ✅ Set up automated Gmail monitoring alerts")
    print("   ✅ Configure SMTP for email notifications")
    print("   ✅ Fix Meeting Processor HTTP 400 error")
    print()
    
    return monitoring_result, token_status

if __name__ == "__main__":
    run_gmail_monitoring_demo()