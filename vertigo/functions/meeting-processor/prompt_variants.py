"""
Prompt variants for meeting transcript analysis.
These can be used to test different approaches for various transcript types and lengths.
"""

def get_prompt_variant(variant_name: str, transcript: str, project: str) -> str:
    """Get a specific prompt variant for meeting analysis."""
    
    if variant_name == "detailed_extraction":
        return detailed_extraction_prompt(transcript, project)
    elif variant_name == "executive_summary":
        return executive_summary_prompt(transcript, project)
    elif variant_name == "technical_focus":
        return technical_focus_prompt(transcript, project)
    elif variant_name == "action_oriented":
        return action_oriented_prompt(transcript, project)
    elif variant_name == "risk_assessment":
        return risk_assessment_prompt(transcript, project)
    elif variant_name == "daily_summary":
        return daily_summary_prompt(transcript, project)
    else:
        return detailed_extraction_prompt(transcript, project)  # Default

def detailed_extraction_prompt(transcript: str, project: str) -> str:
    """Comprehensive extraction with maximum detail preservation."""
    return f"""
You are an expert meeting analyst specializing in technical project management. Extract comprehensive, structured information from this transcript for project {project}.

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
{transcript[:4000]}...

Return only valid JSON. Do not include any explanatory text outside the JSON object. Do not include comments (// or /* */) within the JSON. Ensure all JSON is properly formatted without trailing commas.
"""

def executive_summary_prompt(transcript: str, project: str) -> str:
    """Focused on high-level insights and strategic decisions."""
    return f"""
You are an executive meeting analyst. Create a strategic summary from this transcript for project {project}, focusing on high-level insights and decisions.

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
{transcript[:4000]}...

Return only valid JSON.
"""

def technical_focus_prompt(transcript: str, project: str) -> str:
    """Emphasizes technical details, architecture, and implementation."""
    return f"""
You are a technical meeting analyst. Extract technical details and implementation specifics from this transcript for project {project}.

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
{transcript[:4000]}...

Return only valid JSON.
"""

def action_oriented_prompt(transcript: str, project: str) -> str:
    """Prioritizes action items, deliverables, and next steps."""
    return f"""
You are an action-oriented meeting analyst. Extract all commitments, deliverables, and next steps from this transcript for project {project}.

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
{transcript[:4000]}...

Return only valid JSON.
"""

def risk_assessment_prompt(transcript: str, project: str) -> str:
    """Emphasizes risk identification, mitigation, and contingency planning."""
    return f"""
You are a risk assessment specialist. Identify all risks, blockers, and mitigation strategies from this transcript for project {project}.

Return your response as a JSON object:

{{
    "meeting_summary": "Overview with focus on risk context",
    "high_risk_items": [
        {{
            "risk": "High-risk item",
            "probability": "High/Medium/Low",
            "impact": "High/Medium/Low",
            "mitigation": "Mitigation strategy",
            "owner": "Who owns the risk"
        }}
    ],
    "blockers": [
        {{
            "blocker": "What's blocking progress",
            "impact": "High/Medium/Low",
            "resolution": "How to resolve",
            "escalation": "Who to escalate to"
        }}
    ],
    "assumptions": [
        {{
            "assumption": "Assumption made",
            "validation_needed": "Yes/No",
            "risk_if_wrong": "What happens if assumption is wrong"
        }}
    ],
    "contingency_plans": [
        "Backup plans if things go wrong"
    ],
    "dependencies": [
        {{
            "dependency": "What we depend on",
            "risk_level": "High/Medium/Low",
            "mitigation": "How to reduce risk"
        }}
    ],
    "timeline_risks": [
        "Risks to timeline and delivery"
    ],
    "resource_risks": [
        "Risks related to people, budget, tools"
    ],
    "technical_risks": [
        "Technology and implementation risks"
    ]
}}

Focus on:
- Risk identification and assessment
- Mitigation strategies and contingency plans
- Blockers and escalation paths
- Assumptions and validation needs
- Timeline and resource risks

Transcript:
{transcript[:4000]}...

Return only valid JSON.
""" 

def daily_summary_prompt(transcript: str, project: str) -> str:
    """Generate a concise daily summary for 3:00 PM boss updates."""
    return f"""
You are a professional assistant creating a daily summary for a boss update. Create a concise, professional summary from this daily activity/meeting content for project {project}.

The summary should follow this structure:

**My Ambition:**
[1-2 sentences about the overall goal or strategic focus for the day/week]

**What We Did Today:**
[Bullet points of specific accomplishments, progress made, and key activities completed today]

**What We'll Do Next:**
[Bullet points of immediate next steps, priorities for tomorrow/this week, and upcoming milestones]

Return your response as a JSON object:

{{
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
        {{
            "issue": "What's blocking progress or causing concern",
            "impact": "High/Medium/Low",
            "action_needed": "What the boss can do to help"
        }}
    ],
    "team_coordination": [
        "People you worked with or need to sync with",
        "Cross-team dependencies or collaborations"
    ]
}}

Focus on:
- Clear, actionable language
- Specific accomplishments and progress
- Realistic next steps with clear ownership
- Professional tone suitable for executive communication
- Highlighting team collaboration and dependencies
- Identifying any blockers that need boss attention

Content:
{transcript}

Return only valid JSON. Keep the summary concise and actionable, matching the professional format shown above.
""" 
# A/B Tested Winning Variant - 2025-07-31

def optimized_meeting_summary_prompt(transcript: str, project: str) -> str:
    """Generate a comprehensive meeting summary using A/B tested winning variant."""
    return f"""Create a comprehensive meeting summary from this transcript.

Include:
- Executive summary of main topics
- Detailed discussion points with context
- Specific action items with deadlines and owners
- Key decisions and rationale
- Risks and blockers identified
- Next steps with timeline
- Participant contributions

Format as a detailed report with clear sections and bullet points.

Content:
{transcript}

Return a comprehensive meeting summary following the detailed format above.
"""
