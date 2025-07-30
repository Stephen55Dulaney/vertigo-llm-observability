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
        
        # Remove common reply/forward prefixes
        if subject_lower.startswith('re:'):
            subject_lower = subject_lower[3:].strip()
        elif subject_lower.startswith('fwd:'):
            subject_lower = subject_lower[4:].strip()
        
        # Check for Vertigo prefix
        if subject_lower.startswith('vertigo:'):
            subject_lower = subject_lower[8:].strip()
        
        print(f"DEBUG: Final subject after parsing: '{subject_lower}'")
        
        # Find matching command
        for command, handler in self.commands.items():
            print(f"DEBUG: Checking command '{command}' against '{subject_lower}'")
            if subject_lower.startswith(command):
                print(f"DEBUG: Match found for command '{command}'")
                try:
                    result = handler(subject_lower, body)
                    print(f"DEBUG: Handler returned: {result}")
                    return result
                except Exception as e:
                    print(f"DEBUG: Exception in handler: {e}")
                    logger.error(f"Error handling command '{command}': {e}")
                    return self.create_error_response(f"Error processing command: {e}")
        
        print(f"DEBUG: No command matched")
        return None  # No command matched
    
    def handle_help(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle help command."""
        return {
            'subject': 'Vertigo: Help - Available Commands',
            'body': '''
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
''',
            'command': 'help'
        }
    
    def handle_list_this_week(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle list this week command."""
        try:
            if not self.db:
                return self.create_error_response("Firestore connection failed")
            
            transcript_stats = get_transcript_stats(self.db, days=7)
            meeting_stats = get_meeting_stats(self.db, days=7)
            
            response = "📊 Last 7 Days Summary\n"
            response += "=" * 30 + "\n\n"
            
            response += "📝 Transcripts:\n"
            for project, count in transcript_stats['projects'].items():
                response += f"• {project}: {count} transcripts\n"
            
            response += f"\n📅 Total Transcripts: {transcript_stats['total']}\n"
            response += f"📊 Success Rate: {transcript_stats['success_rate']:.1f}%\n"
            
            response += "\n🤝 Meetings:\n"
            for project, count in meeting_stats['projects'].items():
                response += f"• {project}: {count} meetings\n"
            
            response += f"\n📅 Total Meetings: {meeting_stats['total']}\n"
            
            return {
                'subject': 'Vertigo: Last 7 Days Summary',
                'body': response,
                'command': 'list this week'
            }
        except Exception as e:
            logger.error(f"Error in list_this_week: {e}")
            return self.create_error_response(f"Error getting weekly stats: {e}")
    
    def handle_total_stats(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle total stats command."""
        try:
            if not self.db:
                return self.create_error_response("Firestore connection failed")
            
            transcript_stats = get_transcript_stats(self.db)
            meeting_stats = get_meeting_stats(self.db)
            
            response = "📊 All-Time Statistics\n"
            response += "=" * 25 + "\n\n"
            
            response += "📝 Transcripts:\n"
            for project, count in transcript_stats['projects'].items():
                response += f"• {project}: {count} transcripts\n"
            
            response += f"\n📅 Total Transcripts: {transcript_stats['total']}\n"
            response += f"📊 Success Rate: {transcript_stats['success_rate']:.1f}%\n"
            
            response += "\n🤝 Meetings:\n"
            for project, count in meeting_stats['projects'].items():
                response += f"• {project}: {count} meetings\n"
            
            response += f"\n📅 Total Meetings: {meeting_stats['total']}\n"
            
            return {
                'subject': 'Vertigo: All-Time Statistics',
                'body': response,
                'command': 'total stats'
            }
        except Exception as e:
            logger.error(f"Error in total_stats: {e}")
            return self.create_error_response(f"Error getting total stats: {e}")
    
    def handle_list_projects(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle list projects command."""
        try:
            if not self.db:
                return self.create_error_response("Firestore connection failed")
            
            transcript_stats = get_transcript_stats(self.db)
            meeting_stats = get_meeting_stats(self.db)
            
            response = "📋 Project Summary\n"
            response += "=" * 15 + "\n\n"
            
            all_projects = set(transcript_stats['projects'].keys()) | set(meeting_stats['projects'].keys())
            
            for project in sorted(all_projects):
                transcript_count = transcript_stats['projects'].get(project, 0)
                meeting_count = meeting_stats['projects'].get(project, 0)
                response += f"📁 {project}:\n"
                response += f"   • Transcripts: {transcript_count}\n"
                response += f"   • Meetings: {meeting_count}\n\n"
            
            return {
                'subject': 'Vertigo: Project Summary',
                'body': response,
                'command': 'list projects'
            }
        except Exception as e:
            logger.error(f"Error in list_projects: {e}")
            return self.create_error_response(f"Error getting project list: {e}")
    
    def handle_prompt_report(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle prompt report command."""
        response = "🤖 Prompt Report\n"
        response += "=" * 15 + "\n\n"
        response += "This feature is coming soon!\n\n"
        response += "The prompt report will show:\n"
        response += "• Performance metrics for each prompt\n"
        response += "• Cost analysis and optimization suggestions\n"
        response += "• A/B testing results\n"
        response += "• Usage patterns and trends\n\n"
        response += "Check the Vertigo Debug Toolkit dashboard for current prompt analytics."
        
        return {
            'subject': 'Vertigo: Prompt Report (Coming Soon)',
            'body': response,
            'command': 'prompt report'
        }
    
    def create_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            'subject': 'Vertigo: Error',
            'body': f"❌ Error: {error_msg}\n\nSend 'Vertigo: Help' for available commands.",
            'command': 'error'
        }

def test_commands():
    """Test the EmailCommandParser locally."""
    parser = EmailCommandParser()
    print("Testing 'Vertigo: List this week'")
    print(parser.parse_command("Vertigo: List this week"))
    print("\nTesting 'Total stats'")
    print(parser.parse_command("Total stats"))
    print("\nTesting 'Vertigo: Help'")
    print(parser.parse_command("Vertigo: Help"))

if __name__ == "__main__":
    test_commands() 