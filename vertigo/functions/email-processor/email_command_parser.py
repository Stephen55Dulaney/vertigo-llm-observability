#!/usr/bin/env python3
"""
Email Command Parser for Vertigo
Handle email subject line commands for transcript statistics and operations.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from firestore_stats import get_firestore_client, get_transcript_stats, get_meeting_stats

logger = logging.getLogger(__name__)

class EmailCommandParser:
    """Parse email subject lines for Vertigo commands."""
    
    def __init__(self):
        self.db = get_firestore_client()
        self.commands = {
            'list this week': self.handle_list_this_week,
            'total stats': self.handle_total_stats,
            'list projects': self.handle_list_projects,
            'help': self.handle_help,
            'prompt report': self.handle_prompt_report
        }
    
    def parse_command(self, subject: str, body: str = "") -> Optional[Dict[str, Any]]:
        """Parse email subject and return command response."""
        subject_lower = subject.lower().strip()
        
        # Check for Vertigo prefix
        if subject_lower.startswith('vertigo:'):
            subject_lower = subject_lower[8:].strip()
        
        # Find matching command
        for command, handler in self.commands.items():
            if subject_lower.startswith(command):
                try:
                    return handler(subject_lower, body)
                except Exception as e:
                    logger.error(f"Error handling command '{command}': {e}")
                    return self.create_error_response(f"Error processing command: {e}")
        
        return None  # No command matched
    
    def handle_list_this_week(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle 'list this week' command."""
        if not self.db:
            return self.create_error_response("Firestore connection failed")
        
        transcript_stats = get_transcript_stats(self.db, days=7)
        meeting_stats = get_meeting_stats(self.db, days=7)
        
        response_body = self.format_weekly_stats(transcript_stats, meeting_stats)
        
        return {
            'subject': 'Vertigo: This Week\'s Statistics',
            'body': response_body,
            'command': 'list_this_week'
        }
    
    def handle_total_stats(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle 'total stats' command."""
        if not self.db:
            return self.create_error_response("Firestore connection failed")
        
        transcript_stats = get_transcript_stats(self.db)
        meeting_stats = get_meeting_stats(self.db)
        
        response_body = self.format_total_stats(transcript_stats, meeting_stats)
        
        return {
            'subject': 'Vertigo: Total Statistics',
            'body': response_body,
            'command': 'total_stats'
        }
    
    def handle_list_projects(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle 'list projects' command."""
        if not self.db:
            return self.create_error_response("Firestore connection failed")
        
        transcript_stats = get_transcript_stats(self.db)
        
        if not transcript_stats or not transcript_stats.get('projects'):
            return self.create_error_response("No projects found")
        
        response_body = self.format_projects_list(transcript_stats['projects'])
        
        return {
            'subject': 'Vertigo: Projects List',
            'body': response_body,
            'command': 'list_projects'
        }
    
    def handle_help(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle 'help' command."""
        help_text = """
Vertigo Email Commands
=====================

Available Commands:
• "Vertigo: List this week" - Show transcripts and meetings from the last 7 days
• "Vertigo: Total stats" - Show all-time statistics
• "Vertigo: List projects" - Show all projects with transcript counts
• "Vertigo: Help" - Show this help message

Usage:
Send an email to vertigo.agent.2025@gmail.com with one of the above subjects.

Examples:
Subject: "Vertigo: List this week"
Subject: "Vertigo: Total stats"
Subject: "Vertigo: List projects"

Note: Commands are case-insensitive and can be sent with or without the "Vertigo:" prefix.
"""
        
        return {
            'subject': 'Vertigo: Help - Available Commands',
            'body': help_text,
            'command': 'help'
        }
    
    def handle_prompt_report(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle 'prompt report' command."""
        # This would integrate with your prompt evaluation system
        response_body = """
Prompt Evaluation Report
=======================

This feature is under development. The prompt evaluation system will provide:
• A/B testing results between prompt versions
• Cost optimization recommendations
• Performance metrics for each prompt
• Session analysis and conversation flow tracking

To access prompt evaluation features, visit:
http://localhost:8080/dashboard/advanced-evaluation

For now, you can use the dashboard to:
• View prompt performance metrics
• Compare different prompt versions
• Get cost optimization recommendations
• Analyze session patterns
"""
        
        return {
            'subject': 'Vertigo: Prompt Evaluation Report',
            'body': response_body,
            'command': 'prompt_report'
        }
    
    def format_weekly_stats(self, transcript_stats: Dict, meeting_stats: Dict) -> str:
        """Format weekly statistics for email response."""
        body = f"""
This Week's Statistics (Last 7 Days)
====================================

Transcripts:
• Total: {transcript_stats.get('total_transcripts', 0) if transcript_stats else 0}
• Projects: {transcript_stats.get('unique_projects', 0) if transcript_stats else 0}
• Types: {', '.join([f"{k} ({v})" for k, v in transcript_stats.get('transcript_types', {}).items()]) if transcript_stats else 'None'}

Meetings:
• Total: {meeting_stats.get('total_meetings', 0) if meeting_stats else 0}
• Status: {', '.join([f"{k} ({v})" for k, v in meeting_stats.get('meeting_status', {}).items()]) if meeting_stats else 'None'}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return body
    
    def format_total_stats(self, transcript_stats: Dict, meeting_stats: Dict) -> str:
        """Format total statistics for email response."""
        body = f"""
All-Time Statistics
==================

Transcripts:
• Total: {transcript_stats.get('total_transcripts', 0) if transcript_stats else 0}
• Projects: {transcript_stats.get('unique_projects', 0) if transcript_stats else 0}
• Types: {', '.join([f"{k} ({v})" for k, v in transcript_stats.get('transcript_types', {}).items()]) if transcript_stats else 'None'}

Meetings:
• Total: {meeting_stats.get('total_meetings', 0) if meeting_stats else 0}
• Status: {', '.join([f"{k} ({v})" for k, v in meeting_stats.get('meeting_status', {}).items()]) if meeting_stats else 'None'}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return body
    
    def format_projects_list(self, projects: list) -> str:
        """Format projects list for email response."""
        body = f"""
Projects List
============

Total Projects: {len(projects)}

Projects:
{chr(10).join([f"• {project}" for project in projects])}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return body
    
    def create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            'subject': 'Vertigo: Error',
            'body': f"""
Error Processing Command
=======================

{error_message}

Please try again or contact support if the issue persists.

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""",
            'command': 'error'
        }

def test_commands():
    """Test the command parser with sample commands."""
    parser = EmailCommandParser()
    
    test_commands = [
        "Vertigo: List this week",
        "Vertigo: Total stats",
        "Vertigo: List projects",
        "Vertigo: Help",
        "list this week",
        "total stats",
        "help"
    ]
    
    print("🧪 Testing Email Command Parser")
    print("=" * 50)
    
    for command in test_commands:
        print(f"\n📧 Testing: '{command}'")
        result = parser.parse_command(command)
        
        if result:
            print(f"✅ Command recognized: {result['command']}")
            print(f"📋 Subject: {result['subject']}")
            print(f"📄 Body preview: {result['body'][:100]}...")
        else:
            print("❌ Command not recognized")
    
    print("\n✅ Command parser testing completed!")

if __name__ == "__main__":
    test_commands() 