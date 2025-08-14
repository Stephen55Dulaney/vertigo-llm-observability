#!/usr/bin/env python3
"""
Reload prompts with fixed content.
"""

from app import create_app, db
from app.models import Prompt, User

def reload_prompts():
    """Reload prompts with fixed content."""
    app = create_app()
    
    with app.app_context():
        # Get admin user
        admin_user = User.query.filter_by(email='admin@vertigo.com').first()
        if not admin_user:
            print("❌ Admin user not found")
            return
        
        # Delete existing prompts
        Prompt.query.delete()
        db.session.commit()
        print("🗑️ Deleted existing prompts")
        
        # Define the fixed prompts
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

{{
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
        {{
            "description": "Strategic action item",
            "owner": "Person responsible",
            "due_date": "Date if mentioned",
            "priority": "High/Medium/Low"
        }}
    ],
    "risks": [
        {{
            "risk": "Strategic risk",
            "impact": "High/Medium/Low",
            "mitigation": "Mitigation strategy"
        }}
    ],
    "next_quarter_focus": [
        "Strategic priorities for next quarter"
    ],
    "stakeholders": [
        "Key stakeholders involved"
    ]
}}

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

Return your response as a JSON object:

{{
    "daily_summary": "Concise summary of today's key activities and outcomes",
    "key_accomplishments": [
        "Major accomplishment 1",
        "Major accomplishment 2"
    ],
    "ongoing_work": [
        "Work in progress",
        "Current initiatives"
    ],
    "blockers": [
        "Any issues or blockers encountered"
    ],
    "next_steps": [
        "What's planned for tomorrow"
    ],
    "status": "On Track/At Risk/Behind Schedule"
}}

Focus on:
- Key accomplishments and progress made
- Important decisions or insights
- Any blockers or issues that need attention
- Clear next steps and priorities

Content:
{transcript}

Return only valid JSON."""
            },
            {
                "name": "Technical Focus",
                "version": "1.0",
                "prompt_type": "meeting_analysis",
                "tags": ["technical", "architecture", "implementation"],
                "content": """You are a technical meeting analyst. Extract technical details and implementation specifics from this transcript for project {project}.

Return your response as a JSON object:

{{
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
        {{
            "risk": "Technical risk",
            "impact": "High/Medium/Low",
            "mitigation": "Technical solution"
        }}
    ],
    "action_items": [
        {{
            "description": "Technical task",
            "owner": "Person responsible",
            "due_date": "Date if mentioned",
            "complexity": "High/Medium/Low"
        }}
    ],
    "dependencies": [
        "Technical dependencies",
        "Integration requirements"
    ],
    "success_metrics": [
        "Performance metrics",
        "Success criteria"
    ]
}}

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

{{
    "meeting_summary": "Brief overview focusing on outcomes",
    "immediate_actions": [
        {{
            "description": "Action to be done this week",
            "owner": "Person responsible",
            "due_date": "Specific date",
            "priority": "Critical/High/Medium/Low"
        }}
    ],
    "deliverables": [
        {{
            "description": "Specific deliverable",
            "owner": "Person responsible",
            "due_date": "Date if mentioned",
            "type": "Document/Code/Design/Research"
        }}
    ],
    "next_week_focus": [
        "Priority items for next week"
    ],
    "blockers": [
        {{
            "blocker": "What's blocking progress",
            "owner": "Who can resolve it",
            "escalation_needed": "Yes/No"
        }}
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
}}

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
        
        db.session.commit()
        print(f"✅ Successfully loaded {loaded_count} prompts with fixed content!")
        print("📋 The prompts should now work without formatting errors.")

if __name__ == "__main__":
    reload_prompts() 