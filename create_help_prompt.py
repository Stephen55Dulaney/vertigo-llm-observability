#!/usr/bin/env python3
"""
Create a Help prompt for the Vertigo system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Prompt, db

def create_help_prompt():
    """Create a Help prompt in the database."""
    
    app = create_app()
    
    with app.app_context():
        # Check if help prompt already exists
        existing_help = Prompt.query.filter_by(name="Help").first()
        if existing_help:
            print("Help prompt already exists!")
            return
        
        # Create the Help prompt
        help_prompt = Prompt(
            name="Help",
            content="""You are Vertigo, an AI assistant that helps manage transcripts, meetings, and project data.

When someone asks for help, provide a comprehensive overview of your capabilities:

AVAILABLE COMMANDS:
• "List this week" - Show transcripts and meetings from the last 7 days
• "Total stats" - Show all-time statistics  
• "List projects" - Show all projects with transcript counts
• "Help" - Show this help message
• "Prompt report" - Generate prompt analytics report

USAGE:
Send an email to vertigo.agent.2025@gmail.com with one of the above subjects.

EXAMPLES:
Subject: "Vertigo: List this week"
Subject: "Vertigo: Total stats" 
Subject: "Vertigo: List projects"

FEATURES:
• Email-based command interface
• Transcript and meeting management
• Project organization
• Statistical reporting
• Prompt evaluation and analytics

For advanced features, visit the Vertigo Debug Toolkit dashboard.

Note: Commands are case-insensitive and can be sent with or without the "Vertigo:" prefix.""",
            prompt_type="help",
            version="1.0",
            description="Help prompt for explaining Vertigo capabilities and available commands",
            tags="help,commands,assistance,guidance",
            creator_id=1
        )
        
        db.session.add(help_prompt)
        db.session.commit()
        
        print("✅ Help prompt created successfully!")
        print(f"Prompt ID: {help_prompt.id}")
        print(f"Name: {help_prompt.name}")
        print(f"Type: {help_prompt.prompt_type}")

if __name__ == "__main__":
    create_help_prompt() 