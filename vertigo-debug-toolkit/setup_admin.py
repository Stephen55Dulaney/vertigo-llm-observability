#!/usr/bin/env python3
"""
Setup script for Vertigo Debug Toolkit.
Creates admin user and loads existing prompts.
"""

import os
import sys
import getpass
import secrets
import string
from app import create_app, db
from app.models import User, Prompt

def validate_password(password):
    """Validate password strength."""
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not (has_upper and has_lower and has_digit and has_special):
        return False, "Password must contain uppercase, lowercase, number, and special character"
    
    # Check for common weak passwords
    weak_patterns = ['password', '123456', 'admin', 'qwerty', 'letmein']
    if any(pattern in password.lower() for pattern in weak_patterns):
        return False, "Password contains common weak patterns"
    
    return True, "Password is strong"

def generate_secure_password():
    """Generate a cryptographically secure password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    return ''.join(secrets.choice(alphabet) for _ in range(16))

def create_admin_user():
    """Create admin user with secure password requirements."""
    app = create_app()
    
    with app.app_context():
        email = os.getenv('ADMIN_EMAIL')
        password = os.getenv('ADMIN_PASSWORD')
        
        # Check if admin user already exists
        existing_user = User.query.filter_by(email=email).first() if email else None
        if existing_user:
            print(f"✅ Admin user {email} already exists")
            return existing_user
        
        # Interactive setup if no environment variables
        if not email:
            email = input("Enter admin email (default: admin@vertigo.local): ").strip()
            if not email:
                email = "admin@vertigo.local"
        
        if not password:
            print("\n🔒 Password Requirements:")
            print("   • At least 12 characters")
            print("   • Upper and lowercase letters")
            print("   • Numbers and special characters")
            print("   • No common weak patterns")
            
            use_generated = input("\nGenerate secure password? (y/N): ").strip().lower()
            if use_generated == 'y':
                password = generate_secure_password()
                print(f"\n🔑 Generated password: {password}")
                print("⚠️  SAVE THIS PASSWORD SECURELY - it won't be shown again!")
                input("Press Enter when you've saved the password...")
            else:
                while True:
                    password = getpass.getpass("Enter admin password: ")
                    is_valid, message = validate_password(password)
                    if is_valid:
                        confirm_password = getpass.getpass("Confirm password: ")
                        if password == confirm_password:
                            break
                        else:
                            print("❌ Passwords don't match. Try again.")
                    else:
                        print(f"❌ {message}")
        else:
            # Validate environment password
            is_valid, message = validate_password(password)
            if not is_valid:
                print(f"❌ Environment password is weak: {message}")
                print("Please set ADMIN_PASSWORD to a stronger password")
                sys.exit(1)
        
        # Create user
        user = User(
            email=email,
            username='admin',
            is_admin=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        print(f"✅ Admin user {email} created successfully")
        return user

def load_existing_prompts():
    """Load existing prompts from the meeting processor."""
    app = create_app()
    
    with app.app_context():
        # Define the existing prompts from prompt_variants.py
        existing_prompts = [
            {
                "name": "Detailed Extraction",
                "version": "1.0",
                "prompt_type": "meeting_analysis",
                "tags": ["comprehensive", "structured", "technical"],
                "content": """You are an expert meeting analyst specializing in technical project management. Extract comprehensive, structured information from this transcript for project {project}.

IMPORTANT: Return your response as a JSON object with the following structure:

{{
    "meeting_summary": "2-3 sentence overview of what was discussed",
    "key_points": [
        "Important point 1",
        "Important point 2"
    ],
    "action_items": [
        {{
            "description": "Specific action item",
            "owner": "Person responsible",
            "due_date": "Date if mentioned, otherwise null",
            "confidence": "CONFIRMED/PROPOSED/EXPLORATORY"
        }}
    ],
    "technical_details": [
        "Technical stack mentioned",
        "Architecture decisions",
        "Performance metrics",
        "Timeline estimates"
    ],
    "risks": [
        {{
            "risk": "Description of risk",
            "impact": "High/Medium/Low",
            "mitigation": "Proposed solution if mentioned"
        }}
    ],
    "decisions": [
        "Decision 1",
        "Decision 2"
    ],
    "assumptions": [
        "Assumption 1",
        "Assumption 2"
    ],
    "project_names": [
        "Explicit project names mentioned"
    ],
    "participants": [
        "List of people who spoke"
    ],
    "next_steps": [
        "What needs to happen next"
    ]
}}

EXTRACTION GUIDELINES:
1. Extract ALL commitments made during the meeting, including specific deliverables, prototypes, research tasks, and timeline commitments
2. Maintain technical specificity - preserve technology stack choices, architecture decisions, performance metrics, and development phases
3. Distinguish between: CONFIRMED decisions, PROPOSED options, EXPLORATORY ideas, and ASSUMPTIONS that need validation
4. Identify project names explicitly mentioned and maintain context boundaries
5. Capture risks, blockers, and proposed solutions with impact levels
6. Preserve timeline estimates and due dates mentioned

Transcript:
{transcript}

Return only valid JSON. Do not include any explanatory text outside the JSON object."""
            },
            {
                "name": "Executive Summary",
                "version": "1.0", 
                "prompt_type": "meeting_analysis",
                "tags": ["executive", "strategic", "high-level"],
                "content": """You are an executive meeting analyst. Create a strategic summary from this transcript for project {project}, focusing on high-level insights and decisions.

Return your response as a JSON object:

{
    "meeting_summary": "Executive-level overview of key outcomes",
    "strategic_decisions": [
        "High-level decision 1",
        "High-level decision 2"
    ],
    "business_impact": [
        "Impact on business goals",
        "Resource implications"
    ],
    "action_items": [
        {
            "description": "Strategic action item",
            "owner": "Person responsible",
            "due_date": "Date if mentioned",
            "priority": "High/Medium/Low"
        }
    ],
    "risks": [
        {
            "risk": "Strategic risk",
            "impact": "High/Medium/Low",
            "mitigation": "Mitigation strategy"
        }
    ],
    "next_quarter_focus": [
        "Strategic priorities for next quarter"
    ],
    "stakeholders": [
        "Key stakeholders involved"
    ]
}

Focus on:
- Strategic decisions and their business impact
- Resource allocation and timeline implications
- Risk assessment at the project level
- Alignment with business objectives

Transcript:
{transcript}

Return only valid JSON."""
            },
            {
                "name": "Daily Summary (3:00 PM)",
                "version": "1.0",
                "prompt_type": "daily_summary",
                "tags": ["daily", "boss_update", "executive"],
                "content": """You are a professional assistant creating a daily summary for a boss update. Create a concise, professional summary from this daily activity/meeting content for project {project}.

The summary should follow this structure:

**My Ambition:**
[1-2 sentences about the overall goal or strategic focus for the day/week]

**What We Did Today:**
[Bullet points of specific accomplishments, progress made, and key activities completed today]

**What We'll Do Next:**
[Bullet points of immediate next steps, priorities for tomorrow/this week, and upcoming milestones]

Return your response as a JSON object:

{
    "my_ambition": "Clear statement of strategic focus and goals",
    "what_we_did_today": [
        "Specific accomplishment or progress made",
        "Key activity or milestone completed",
        "Important work done with team members"
    ],
    "what_well_do_next": [
        "Immediate next step or priority",
        "Upcoming milestone or deliverable",
        "Team coordination or planning needed"
    ],
    "key_metrics": [
        "Quantifiable progress indicators",
        "Timeline updates or deadlines"
    ],
    "blockers_risks": [
        {
            "issue": "What's blocking progress or causing concern",
            "impact": "High/Medium/Low",
            "action_needed": "What the boss can do to help"
        }
    ],
    "team_coordination": [
        "People you worked with or need to sync with",
        "Cross-team dependencies or collaborations"
    ]
}

Focus on:
- Clear, actionable language
- Specific accomplishments and progress
- Realistic next steps with clear ownership
- Professional tone suitable for executive communication
- Highlighting team collaboration and dependencies
- Identifying any blockers that need boss attention

Content:
{transcript}

Return only valid JSON. Keep the summary concise and actionable, matching the professional format shown above."""
            },
            {
                "name": "Technical Focus",
                "version": "1.0",
                "prompt_type": "meeting_analysis", 
                "tags": ["technical", "architecture", "implementation"],
                "content": """You are a technical meeting analyst. Extract technical details and implementation specifics from this transcript for project {project}.

Return your response as a JSON object:

{
    "meeting_summary": "Technical overview of what was discussed",
    "architecture_decisions": [
        "Architecture choice 1",
        "Architecture choice 2"
    ],
    "technology_stack": [
        "Technology mentioned",
        "Framework decisions"
    ],
    "technical_requirements": [
        "Performance requirements",
        "Scalability needs",
        "Integration requirements"
    ],
    "implementation_plan": [
        "Development phases",
        "Timeline estimates",
        "Resource needs"
    ],
    "technical_risks": [
        {
            "risk": "Technical risk",
            "impact": "High/Medium/Low",
            "mitigation": "Technical solution"
        }
    ],
    "action_items": [
        {
            "description": "Technical task",
            "owner": "Person responsible",
            "due_date": "Date if mentioned",
            "complexity": "High/Medium/Low"
        }
    ],
    "dependencies": [
        "Technical dependencies",
        "Integration requirements"
    ],
    "success_metrics": [
        "Performance metrics",
        "Success criteria"
    ]
}

Focus on:
- Technical architecture and design decisions
- Technology stack and framework choices
- Implementation details and timelines
- Performance and scalability considerations
- Technical risks and mitigation strategies

Transcript:
{transcript}

Return only valid JSON."""
            },
            {
                "name": "Action Oriented",
                "version": "1.0",
                "prompt_type": "meeting_analysis",
                "tags": ["action", "deliverables", "next_steps"],
                "content": """You are an action-oriented meeting analyst. Extract all commitments, deliverables, and next steps from this transcript for project {project}.

Return your response as a JSON object:

{
    "meeting_summary": "Brief overview focusing on outcomes",
    "immediate_actions": [
        {
            "description": "Action to be done this week",
            "owner": "Person responsible",
            "due_date": "Specific date",
            "priority": "Critical/High/Medium/Low"
        }
    ],
    "deliverables": [
        {
            "description": "Specific deliverable",
            "owner": "Person responsible",
            "due_date": "Date if mentioned",
            "type": "Document/Code/Design/Research"
        }
    ],
    "next_week_focus": [
        "Priority items for next week"
    ],
    "blockers": [
        {
            "blocker": "What's blocking progress",
            "owner": "Who can resolve it",
            "escalation_needed": "Yes/No"
        }
    ],
    "dependencies": [
        "What depends on what"
    ],
    "success_criteria": [
        "How we'll know we're done"
    ],
    "timeline": [
        "Key milestones and dates"
    ]
}

Focus on:
- Specific, actionable commitments
- Clear ownership and due dates
- Blockers and dependencies
- Success criteria and milestones
- Next week's priorities

Transcript:
{transcript}

Return only valid JSON."""
            }
        ]
        
        # Load prompts into database
        loaded_count = 0
        for prompt_data in existing_prompts:
            # Check if prompt already exists
            existing = Prompt.query.filter_by(
                name=prompt_data["name"],
                version=prompt_data["version"]
            ).first()
            
            if not existing:
                # Get admin user for creator_id
                admin_user = User.query.filter_by(is_admin=True).first()
                if not admin_user:
                    print("❌ No admin user found. Please create admin user first.")
                    return
                
                prompt = Prompt(
                    name=prompt_data["name"],
                    version=prompt_data["version"],
                    content=prompt_data["content"],
                    prompt_type=prompt_data["prompt_type"],
                    tags=prompt_data["tags"],
                    creator_id=admin_user.id
                )
                db.session.add(prompt)
                loaded_count += 1
                print(f"✅ Added prompt: {prompt_data['name']}")
            else:
                print(f"⏭️  Prompt already exists: {prompt_data['name']}")
        
        db.session.commit()
        print(f"\n🎉 Successfully loaded {loaded_count} new prompts!")

def main():
    """Main setup function."""
    print("🚀 Setting up Vertigo Debug Toolkit...")
    print("=" * 50)
    print("⚠️  SECURITY NOTICE: Default passwords are no longer allowed!")
    print("   This setup will require a strong password for security.")
    print("=" * 50)
    
    # Create admin user
    print("\n1. Creating admin user...")
    create_admin_user()
    
    # Load prompts
    print("\n2. Loading existing prompts...")
    load_existing_prompts()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\n📝 Login with the credentials you just set up")
    print("⚠️  If you used a generated password, make sure you saved it!")
    print("\n🌐 Access the app at: http://localhost:8080")
    print("📊 Go to: http://localhost:8080/prompts/ to manage prompts")

if __name__ == "__main__":
    main() 