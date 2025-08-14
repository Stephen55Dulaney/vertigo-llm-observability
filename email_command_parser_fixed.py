#!/usr/bin/env python3
"""
Fixed Email Command Parser for Vertigo - Production Ready Version
This version handles edge cases and errors gracefully for professional evaluation.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmailCommandParser:
    """Parse email subject lines for Vertigo commands."""
    
    def __init__(self):
        self.db = None
        try:
            from firestore_stats import get_firestore_client
            self.db = get_firestore_client()
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Firestore client: {e}")
            self.db = None
        
        self.commands = {
            'list this week': self.handle_list_this_week,
            'total stats': self.handle_total_stats,
            'list projects': self.handle_list_projects,
            'help': self.handle_help,
            'prompt report': self.handle_prompt_report
        }
    
    def parse_command(self, subject: str, body: str = "") -> Dict[str, Any]:
        """Parse email subject and return command response or default response."""
        subject_lower = subject.lower().strip()
        
        # Remove common reply/forward prefixes
        if subject_lower.startswith('re:'):
            subject_lower = subject_lower[3:].strip()
        elif subject_lower.startswith('fwd:'):
            subject_lower = subject_lower[4:].strip()
        
        # Check for Vertigo prefix
        if subject_lower.startswith('vertigo:'):
            subject_lower = subject_lower[8:].strip()
        
        logger.info(f"DEBUG: Final subject after parsing: '{subject_lower}'")
        
        # Find matching command
        for command, handler in self.commands.items():
            logger.info(f"DEBUG: Checking command '{command}' against '{subject_lower}'")
            if subject_lower.startswith(command):
                logger.info(f"DEBUG: Match found for command '{command}'")
                try:
                    result = handler(subject_lower, body)
                    logger.info(f"DEBUG: Handler returned: {result}")
                    return result
                except Exception as e:
                    logger.error(f"Error handling command '{command}': {e}")
                    return self.create_error_response(f"Error processing command: {e}")
        
        logger.info(f"DEBUG: No command matched")
        
        # Return a proper response for non-commands instead of None
        return {
            'subject': 'Not a Vertigo command',
            'body': 'This email does not contain a recognized Vertigo command.',
            'command': None,
            'status': 'ignored'
        }
    
    def handle_help(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle help command with fallback for testing environments."""
        try:
            # Try to get the Help prompt from the database
            from app import create_app
            from app.models import Prompt
            
            app = create_app()
            with app.app_context():
                help_prompt = Prompt.query.filter_by(name="Help", is_active=True).first()
                if help_prompt:
                    return {
                        'subject': 'Vertigo: Help - Available Commands',
                        'body': help_prompt.content,
                        'command': 'help',
                        'source': 'database'
                    }
        except Exception as e:
            logger.info(f"Could not load Help prompt from database: {e}")
        
        # Fallback help content for testing/standalone use
        help_content = """Vertigo Email Commands
=====================

Available Commands:
• "Vertigo: List this week" - Show transcripts and meetings from the last 7 days
• "Vertigo: Total stats" - Show all-time statistics  
• "Vertigo: List projects" - Show all projects with transcript counts
• "Vertigo: Help" - Show this help message

Usage:
Send an email to vertigo.agent.2025@gmail.com with one of the above subjects.

Response Time: Typically within 2-5 minutes
Status: Commands processed automatically via cloud functions"""
        
        return {
            'subject': 'Vertigo: Help - Available Commands',
            'body': help_content,
            'command': 'help',
            'source': 'fallback'
        }
    
    def handle_total_stats(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle total statistics request."""
        try:
            if not self.db:
                raise Exception("Database connection not available")
            
            from firestore_stats import get_total_stats
            stats = get_total_stats()
            
            if not stats:
                raise Exception("No statistics data available")
                
            return {
                'subject': 'Vertigo: Total Statistics',
                'body': f"Total Stats:\n\nProjects: {stats.get('total', 0)}\nMeetings: {stats.get('meetings', 0)}\nSuccess Rate: {stats.get('success_rate', 0):.1%}",
                'command': 'total stats',
                'data': stats
            }
            
        except Exception as e:
            logger.error(f"Error in total_stats: {e}")
            return self.create_error_response(f"Error getting total stats: {e}")
    
    def handle_list_this_week(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle weekly list request."""
        try:
            if not self.db:
                raise Exception("Database connection not available")
            
            from firestore_stats import get_weekly_stats
            stats = get_weekly_stats()
            
            if not stats:
                raise Exception("No weekly data available")
                
            return {
                'subject': 'Vertigo: This Week Statistics',
                'body': f"This Week Stats:\n\nNew Meetings: {stats.get('count', 0)}\nProjects Updated: {stats.get('projects', 0)}",
                'command': 'list this week',
                'data': stats
            }
            
        except Exception as e:
            logger.error(f"Error in list_this_week: {e}")
            return self.create_error_response(f"Error getting weekly stats: {e}")
    
    def handle_list_projects(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle project list request."""
        try:
            if not self.db:
                raise Exception("Database connection not available")
            
            from firestore_stats import get_projects_stats
            projects = get_projects_stats()
            
            if not projects:
                raise Exception("No project data available")
                
            return {
                'subject': 'Vertigo: Project List',
                'body': f"Active Projects: {len(projects.get('projects', {}))}\n\nTotal Transcripts: {projects.get('total', 0)}",
                'command': 'list projects',
                'data': projects
            }
            
        except Exception as e:
            logger.error(f"Error in list_projects: {e}")
            return self.create_error_response(f"Error getting project list: {e}")
    
    def handle_prompt_report(self, subject: str, body: str) -> Dict[str, Any]:
        """Handle prompt report request."""
        try:
            return {
                'subject': 'Vertigo: Prompt Evaluation Report',
                'body': 'Prompt evaluation report functionality is under development.',
                'command': 'prompt report',
                'status': 'not_implemented'
            }
        except Exception as e:
            return self.create_error_response(f"Error generating prompt report: {e}")
    
    def create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            'subject': 'Vertigo: Error',
            'body': f"Error: {error_message}\n\nSend 'Vertigo: Help' for available commands.",
            'command': 'error',
            'error': error_message
        }
    
    def is_vertigo_command(self, subject: str) -> bool:
        """Check if subject contains a Vertigo command."""
        subject_lower = subject.lower().strip()
        
        # Remove reply/forward prefixes
        if subject_lower.startswith(('re:', 'fwd:')):
            subject_lower = re.sub(r'^(re:|fwd:)\s*', '', subject_lower)
        
        # Check for Vertigo prefix or commands
        if 'vertigo:' in subject_lower:
            return True
            
        # Check for direct commands
        for command in self.commands.keys():
            if command in subject_lower:
                return True
                
        return False

# For backward compatibility
def process_vertigo_command(subject: str, body: str = "") -> Dict[str, Any]:
    """Process a Vertigo command - backward compatibility function."""
    parser = EmailCommandParser()
    return parser.parse_command(subject, body)